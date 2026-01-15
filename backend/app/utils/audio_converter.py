"""音频格式转换工具 - 使用 ffmpeg 将 WebM 转换为 MP3/WAV。"""

import subprocess
import tempfile
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_webm_to_mp3(audio_data: bytes) -> bytes:
    """
    将 WebM 格式的音频转换为 MP3 格式。
    
    Args:
        audio_data: WebM 格式的音频字节数据
        
    Returns:
        MP3 格式的音频字节数据
        
    Raises:
        RuntimeError: 转换失败时抛出
    """
    return _convert_audio(audio_data, "mp3")


def convert_webm_to_wav(audio_data: bytes) -> bytes:
    """
    将 WebM 格式的音频转换为 WAV 格式。
    
    Args:
        audio_data: WebM 格式的音频字节数据
        
    Returns:
        WAV 格式的音频字节数据
        
    Raises:
        RuntimeError: 转换失败时抛出
    """
    return _convert_audio(audio_data, "wav")


def _convert_audio(audio_data: bytes, output_format: str) -> bytes:
    """
    使用 ffmpeg 转换音频格式。
    
    Args:
        audio_data: 输入音频字节数据
        output_format: 输出格式 (mp3, wav 等)
        
    Returns:
        转换后的音频字节数据
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as input_file:
        input_path = input_file.name
        input_file.write(audio_data)
    
    output_path = input_path.replace(".webm", f".{output_format}")
    
    try:
        # 构建 ffmpeg 命令
        cmd = [
            "ffmpeg",
            "-y",                    # 覆盖输出文件
            "-i", input_path,        # 输入文件
            "-vn",                   # 不处理视频
            "-ar", "16000",          # 采样率 16kHz（ASR 推荐）
            "-ac", "1",              # 单声道
        ]
        
        if output_format == "mp3":
            cmd.extend(["-b:a", "64k"])  # 比特率
        elif output_format == "wav":
            cmd.extend(["-acodec", "pcm_s16le"])  # PCM 16位编码
        
        cmd.append(output_path)
        
        # 执行转换
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"ffmpeg 转换失败: {result.stderr}")
            raise RuntimeError(f"音频格式转换失败: {result.stderr}")
        
        # 读取转换后的文件
        with open(output_path, "rb") as output_file:
            converted_data = output_file.read()
        
        logger.info(
            f"音频转换成功: {len(audio_data)} bytes -> "
            f"{len(converted_data)} bytes ({output_format})"
        )
        
        return converted_data
        
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg 转换超时")
        raise RuntimeError("音频格式转换超时")
        
    finally:
        # 清理临时文件
        for path in [input_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
