import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

#base model
BASE_MODEL_NAME = "microsoft/phi-2"

#saving LoRA files
LORA_PATH = "./lora-weights"

#set device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- Using device: {DEVICE} ---")

#--- load in the model

print("--- Loading base model... ---")
#;load the base model
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_NAME,
    dtype=torch.bfloat16,
    device_map=DEVICE,
    trust_remote_code=True #required for phi-2
)

print("--- Loading tokenizer... ---")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print(f"--- Loading LoRA adapters from {LORA_PATH}... ---")

#Magic step: laoad the PeftModel by "stacking" the LoRA adapters on top of the base model
model = PeftModel.from_pretrained(base_model, LORA_PATH)
model = model.eval()

print("--- Model loading complete! ---")

#---FastAPI App step - pretty easy

app = FastAPI(
    title="Tony Soprano API",
    description="API for generating replies in the voice of Tony Soprano.",
    version="1.0.0"
)

#defines data model for request
class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"message": "Ay-oh! The API is runnin'. Whaddaya want?"}

@app.post("/generate")
async def generate_reply(request: PromptRequest):
    """
    Takes a user prompt and returns a Tony Soprano-style response.
    """
    try:

        formatted_prompt = f"Instruct: Respond like Tony Soprano.\nUser: {request.prompt}\nOutput:"

        #tokenize the input
        inputs = tokenizer(
            formatted_prompt, 
            return_tensors="pt", 
            return_attention_mask=True
        ).to(DEVICE)

        #gnerate the response
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=150, #limit the response length
                do_sample=True,
                temperature=0.7, #couldnt play around with these toggles since inference time was too long on my CPU, but seemed to work well regardless
                top_k=50,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id
            )
        
        #decode the output
        response_text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        
        return {"prompt": request.prompt, "response": response_text.strip()}

    except Exception as e:
        print(f"Error during generation: {e}")
        return {"error": f"Internal server error: {e}"}

#allows you to run the app with `python main.py`
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
