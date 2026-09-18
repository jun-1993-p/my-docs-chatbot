import dotenv

dotenv_file = dotenv.find_dotenv()
nvidia_api_key = dotenv.get_key(dotenv_file, "NVIDIA_API_KEY")

from openai import OpenAI

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = nvidia_api_key
)

completion = client.chat.completions.create(
  model="openai/gpt-oss-20b",
  messages=[{"role":"user","content":"어떤 숫자가 더 크지, 9.11 or 9.8?"}],
  temperature=1,
  top_p=1,
  max_tokens=4096,
  stream=False
)

reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
if reasoning:
  print(reasoning)
print(completion.choices[0].message.content)