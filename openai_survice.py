import dotenv

dotenv_file = dotenv.find_dotenv()
nvidia_api_key = dotenv.get_key(dotenv_file, "NVIDIA_API_KEY")

from openai import OpenAI

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = nvidia_api_key
)