#!/usr/bin/env python3
"""서버 실행 스크립트"""
import sys
import os

# 프로젝트 루트를 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    import uvicorn
    from config import Config
    
    print(f"Starting SENSE API server...")
    print(f"Host: {Config.API_HOST}")
    print(f"Port: {Config.API_PORT}")
    print(f"LLM Provider: {Config.LLM_PROVIDER}")
    
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level="info"
    )

