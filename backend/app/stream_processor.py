"""Stream Processor for handling async generators and SSE formatting."""

import json
import asyncio
import logging
from typing import AsyncGenerator, Any
from .models import ConversationEvent

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Processor for handling streaming data."""
    
    @staticmethod
    async def merge_streams(
        *streams: AsyncGenerator[Any, None]
    ) -> AsyncGenerator[Any, None]:
        """
        Merge multiple async generators into one.
        
        Args:
            *streams: Variable number of async generators
            
        Yields:
            Items from all streams as they become available
        """
        # Create tasks for all streams
        tasks = []
        for stream in streams:
            task = asyncio.create_task(StreamProcessor._stream_to_queue(stream))
            tasks.append(task)
        
        # Create a queue to collect items
        queue: asyncio.Queue = asyncio.Queue()
        
        # Start all stream consumers
        consumers = []
        for stream in streams:
            consumer = asyncio.create_task(
                StreamProcessor._consume_stream(stream, queue)
            )
            consumers.append(consumer)
        
        # Yield items from queue
        active_consumers = len(consumers)
        while active_consumers > 0:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.1)
                if item is None:  # Sentinel value indicating stream end
                    active_consumers -= 1
                else:
                    yield item
            except asyncio.TimeoutError:
                # Check if any consumers are still running
                if all(consumer.done() for consumer in consumers):
                    break
        
        # Clean up
        for consumer in consumers:
            if not consumer.done():
                consumer.cancel()
    
    @staticmethod
    async def _consume_stream(
        stream: AsyncGenerator[Any, None],
        queue: asyncio.Queue
    ) -> None:
        """Consume a stream and put items in queue."""
        try:
            async for item in stream:
                await queue.put(item)
        except Exception as e:
            logger.error(f"Error consuming stream: {e}")
        finally:
            await queue.put(None)  # Sentinel value
    
    @staticmethod
    async def _stream_to_queue(stream: AsyncGenerator[Any, None]) -> None:
        """Helper to consume a stream."""
        try:
            async for _ in stream:
                pass
        except Exception as e:
            logger.error(f"Stream error: {e}")
    
    @staticmethod
    def format_sse_event(event: ConversationEvent) -> str:
        """
        Format a ConversationEvent as Server-Sent Event.
        
        Args:
            event: ConversationEvent to format
            
        Returns:
            SSE formatted string
        """
        return event.to_sse_format()
    
    @staticmethod
    async def event_stream(
        events: AsyncGenerator[ConversationEvent, None]
    ) -> AsyncGenerator[str, None]:
        """
        Convert event stream to SSE formatted stream.
        
        Args:
            events: Stream of ConversationEvent objects
            
        Yields:
            SSE formatted strings
        """
        try:
            async for event in events:
                yield StreamProcessor.format_sse_event(event)
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            # Yield error event
            error_event = ConversationEvent(
                type="error",
                data={"message": str(e)},
                session_id=""
            )
            yield StreamProcessor.format_sse_event(error_event)
    
    @staticmethod
    async def buffer_stream(
        stream: AsyncGenerator[str, None],
        buffer_size: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Buffer stream items to reduce overhead.
        
        Args:
            stream: Input stream
            buffer_size: Number of items to buffer
            
        Yields:
            Buffered items
        """
        buffer = []
        async for item in stream:
            buffer.append(item)
            if len(buffer) >= buffer_size:
                yield "".join(buffer)
                buffer = []
        
        # Yield remaining items
        if buffer:
            yield "".join(buffer)
