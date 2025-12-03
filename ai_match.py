from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어 임포트
from pydantic import BaseModel
import json

# ======================================================================
# 1. CORS 설정 추가 (Netlify 주소 허용)
# ======================================================================

app = FastAPI()

# ⚠️ Netlify 주소 및 Render 자체 주소로 CORS 허용 설정
# Netlify 배포가 완료된 최종 주소로 변경해주세요. (예: https://tangerine-piroshki-1ab9ae.netlify.app)
origins = [
    "https://tangerine-piroshki-1ab9ae.netlify.app", # Netlify 배포 주소 (필수)
    "http://localhost:8000", # 로컬 테스트 주소 (선택)
    "https://ai-policy-matcher.onrender.com" # Render 자체 주소 (선택)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================================
# 2. 데이터 구조 정의
# ======================================================================

class UserRequest(BaseModel):
    age: int
    income: int
    asset_req: bool

# ======================================================================
# 3. 정책 데이터 로드
# ======================================================================

# policy_db.json 파일에서 정책 데이터를 로드합니다.
try:
    with open("policy_db.json", "r", encoding="utf-8") as f:
        POLICY_DB = json.load(f)
except FileNotFoundError:
    print("정책 DB 파일을 찾을 수 없습니다: policy_db.json")
    POLICY_DB = []

# ======================================================================
# 4. 정책 매칭 함수
# ======================================================================

def match_policy(user_data: UserRequest, policy_db: list):
    """사용자 조건에 맞는 정책을 필터링합니다."""
    matched_policies = []
    
    for policy in policy_db:
        # 1. 나이 조건 검사
        if user_data.age > policy["AGE_MAX"]:
            continue
        
        # 2. 소득 조건 검사 (INCOME_MAX가 99999인 경우는 제한 없음)
        if user_data.income > policy["INCOME_MAX"]:
            continue
        
        # 3. 무주택 조건 검사
        # 정책이 무주택(ASSET_REQ=True)을 요구하고, 사용자가 무주택이 아닌 경우 탈락
        if policy["ASSET_REQ"] and not user_data.asset_req:
            continue
            
        matched_policies.append(policy)
        
    return matched_policies

# ======================================================================
# 5. FastAPI 엔드포인트
# ======================================================================

@app.get("/")
def read_root():
    """서버 상태 확인용 루트 엔드포인트"""
    return {"message": "FastAPI Server is running. Use /api/match for policy matching."}

@app.post("/api/match")
async def get_policy_match(request: UserRequest):
    """
    사용자 데이터를 받아 조건에 맞는 정책 리스트를 반환합니다.
    """
    if not POLICY_DB:
        raise HTTPException(status_code=500, detail="Policy database not loaded.")
        
    matched_policies = match_policy(request, POLICY_DB)
    
    return {"matched_policies": matched_policies}