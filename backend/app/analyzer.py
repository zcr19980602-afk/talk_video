import cv2
import base64
import json
import logging
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.api_key = api_key
        self.base_url = base_url
        self.segment_duration = 5  # seconds (Demo setting: shorter segments)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def analyze(self, video_path: Path) -> Dict[str, Any]:
        """
        Main entry point for hierarchical analysis.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Step 0 & 1: Segmentation & Keyframe Extraction
        frames_info = self._extract_keyframes(str(video_path))
        logger.info(f"Extracted {len(frames_info)} keyframes from video.")

        # Step 2: Batch Analysis (Concurrent VLM calls)
        segment_tasks = [self._analyze_segment(info) for info in frames_info]
        segments_data = await asyncio.gather(*segment_tasks)
        
        # Filter out failed segments
        segments_data = [s for s in segments_data if s is not None]
        
        # Step 3: Global Summary
        final_report = await self._generate_global_summary(segments_data)
        
        return {
            "file_info": {
                "filename": video_path.name,
                "duration_sec": frames_info[-1]["timestamp_sec"] if frames_info else 0
            },
            "timeline": segments_data,
            "report": final_report
        }

    def _dhash(self, image):
        """
        Calculate DHash (Difference Hash) for an image.
        1. Resize to 9x8 (provides 64 pixels).
        2. Convert to grayscale.
        3. Compare adjacent pixels: if P[x] > P[x+1] -> 1, else 0.
        """
        resized = cv2.resize(image, (9, 8))
        if len(resized.shape) == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized
            
        hash_str = ""
        # 8 rows, 8 columns of difference
        for i in range(8):
            for j in range(8):
                if gray[i, j] > gray[i, j + 1]:
                    hash_str += "1"
                else:
                    hash_str += "0"
        return int(hash_str, 2)

    def _hamming_distance(self, hash1, hash2):
        """Calculate Hamming distance between two hashes."""
        # XOR to find different bits, then count set bits
        return bin(hash1 ^ hash2).count('1')

    def _extract_keyframes(self, video_path: str) -> List[Dict[str, Any]]:
        """
        DHash Strategy:
        1. Read frames sequentially.
        2. Crop ROI (Center).
        3. Compute DHash.
        4. If Hamming Dist > 5 -> Trigger Keyframe.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # ROI: Center 50%
        roi_x = int(width * 0.25)
        roi_y = int(height * 0.25)
        roi_w = int(width * 0.5)
        roi_h = int(height * 0.5)
        
        selected_frames = []
        prev_hash = None
        last_selected_time = -999.0
        
        # Processing step (check every frame or skip some for ultra-speed)
        # Sequence reading is fast, checking every 3rd frame is a good balance
        check_interval = 3 
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % check_interval == 0:
                # 1. Crop ROI
                roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
                
                # 2. Compute DHash
                curr_hash = self._dhash(roi)
                
                is_significant = False
                dist = 0
                
                if prev_hash is not None:
                    dist = self._hamming_distance(prev_hash, curr_hash)
                    # Threshold > 5 as requested
                    if dist > 5:
                        is_significant = True
                else:
                    is_significant = True # Always keep first frame
                
                if is_significant:
                    # Time deduplication: Don't capture again within 1.0 second
                    # unless the change is EXTREMELY huge (scene cut) which we ignore for webcam analysis
                    frame_time = frame_idx / fps
                    if (frame_time - last_selected_time) >= 1.0:
                        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                        img_str = base64.b64encode(buffer).decode('utf-8')
                        
                        selected_frames.append({
                            "timestamp_sec": frame_time,
                            "timestamp_fmt": f"{int(frame_time//60):02d}:{int(frame_time%60):02d}",
                            "image_base64": img_str,
                            "change_score": float(dist) # Use Hamming dist as score
                        })
                        
                        last_selected_time = frame_time
                        # Update ref hash only when we select (trigger reset)
                        # Or should we update every time? 
                        # Updating every time tracks "speed of change". 
                        # Updating only on select tracks "accumulated change" relative to last keyframe.
                        # For "Trigger", comparing to LAST KEYFRAME is better to avoid drift.
                        prev_hash = curr_hash
                
                # If we didn't select, we DO NOT update prev_hash? 
                # Actually for DHash trigger, usually compare to *previous frame* to detecting motion.
                # Let's compare to previous frame to detect instantaneous motion.
                # If comparing to last keyframe, we detect "scene drift".
                # User said: "Check adjacent two frames" (Queue adjacent 2 frames). 
                # So we update prev_hash every check.
                if not is_significant:
                     prev_hash = curr_hash

            frame_idx += 1
            
        cap.release()
        
        # Hard cap for demo
        if len(selected_frames) > 20:
             selected_frames = selected_frames[:20]
             
        logger.info(f"DHash Extraction: Processed {frame_idx} frames. Selected {len(selected_frames)}.")
        return selected_frames

    async def _analyze_segment(self, frame_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call VLM to analyze a single frame. Returns structured JSON.
        """
        prompt = """
        请分析这个视频关键帧，并输出一个合法的 JSON 对象（不要使用 markdown 或代码块格式）。
        **重点关注：仅分析画面正中心的人物的动作。忽略背景和其他人。**
        
        JSON 结构:
        {
          "scene": "简短的场景描述 (中文)",
          "objects": ["中心人物相关的关键物品列表"],
          "action": "中心人物正在做什么动作？(请详细描述)",
          "ocr": "画面中可见的文字 (如有)"
        }
        """
        
        payload = {
            "model": "glm-4v-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": frame_info["image_base64"]}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            "temperature": 0.3,
            "top_p": 0.8
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                res.raise_for_status()
                result = res.json()
                content = result["choices"][0]["message"]["content"]
                
                # Cleanup potential markdown formatting
                content = content.replace("```json", "").replace("```", "").strip()
                
                data = json.loads(content)
                data["timestamp"] = frame_info["timestamp_fmt"]
                return data
        except Exception as e:
            logger.error(f"Failed to analyze segment at {frame_info['timestamp_fmt']}: {e}")
            return None

    async def _generate_global_summary(self, segments: List[Dict[str, Any]]) -> str:
        """
        Step 3: Aggregate segment notes into a final report using LLM.
        """
        if not segments:
            return "No analysis data available."

        # Prepare context
        context_str = json.dumps(segments, ensure_ascii=False, indent=2)
        
        prompt = f"""
        以下是视频分析的时间轴笔记（每 {self.segment_duration} 秒一段）。
        
        数据:
        {context_str}
        
        任务:
        生成一份专业的**中文** Markdown 分析报告。
        **总结重点：聚焦于画面正中心人物的行为变化（只包含包括肢体动作、表情等，非中心人物之外的任何场景都不要分析，不要描述背景）。**
        
        输出格式:
        # 视频智能分析报告
        
        ## 核心摘要 (TL;DR)
        (3-5 句总结中心人物的主要行为)
        
        ## 关键时间轴
        - **[时间戳]**: 动作描述
        
        ## 详细观察
        (总结人物动作细节和场景)
        """
        
        payload = {
            "model": "glm-4-flash", # Use text model for summarization
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers,
                    timeout=60.0 # Longer timeout for summary
                )
                res.raise_for_status()
                result = res.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Failed to generate global summary: {e}")
            return "Failed to generate report."
