import dotenv

# 환경 변수에서 NVIDIA_API_KEY를 가져오기.
dotenv_file = dotenv.find_dotenv()
nvidia_api_key = dotenv.get_key(dotenv_file, "NVIDIA_API_KEY")

from openai import OpenAI

# NVIDIA API 클라이언트 초기화.
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = nvidia_api_key
)