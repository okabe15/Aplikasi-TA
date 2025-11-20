import httpx
import asyncio
from app.config import settings
from app.models.schemas import ComicPanel, ImageGenerationRequest
from typing import List, Dict, Any

class ComfyUIService:
    def __init__(self):
        self.base_url = settings.comfyui_url
    
    # ✅ UPDATED: Add characters parameter
    def build_prompt(self, panel: ComicPanel, characters: List[Dict[str, Any]] = None) -> str:
        """Build image generation prompt from panel with STRONG character consistency"""

        prompt = ""

        # ✅ IMPROVED: More emphatic character consistency instructions
        if characters and len(characters) > 0:
            prompt += "CRITICAL - CHARACTER CONSISTENCY REQUIRED:\n"
            prompt += "USE THESE EXACT CHARACTER DESCRIPTIONS IN EVERY PANEL:\n\n"

            for char in characters:
                char_name = char.get('name', 'Unknown')
                char_desc = char.get('description', '')
                char_role = char.get('role', 'character')

                # ✅ Enhanced formatting with visual markers
                prompt += f"**{char_name}** ({char_role}):\n"
                prompt += f"- MUST LOOK EXACTLY LIKE: {char_desc}\n"
                prompt += f"- SAME FACE, SAME HAIR, SAME CLOTHING in ALL panels\n"
                prompt += f"- Distinctive features: {self._extract_key_features(char_desc)}\n\n"

            prompt += "CONSISTENCY RULES:\n"
            prompt += "- Characters MUST look identical to previous panels\n"
            prompt += "- Maintain exact same facial features, hair style, and clothing\n"
            prompt += "- NO variations in character appearance\n\n"
            prompt += "---\n\n"

        # Scene composition
        prompt += f"SCENE: {panel.composition} showing {panel.visual}"

        if panel.setting:
            prompt += f", LOCATION: {panel.setting}"

        if panel.mood:
            prompt += f", MOOD: {panel.mood}"

        # Style instructions
        prompt += ", western comic book art style, colorful american comic book illustration"
        prompt += ", bold vibrant colors, dynamic shading, comic panel border"
        prompt += ", professional comic book art, detailed illustration, high quality"
        prompt += ", clean composition, consistent character design"

        return prompt

    def _extract_key_features(self, description: str) -> str:
        """Extract key visual features from character description for emphasis"""
        features = []

        # Look for key descriptive words
        keywords = ['hair', 'eyes', 'tall', 'short', 'beard', 'glasses', 'hat', 'dress', 'suit', 'jacket']
        desc_lower = description.lower()

        for keyword in keywords:
            if keyword in desc_lower:
                # Find the phrase containing this keyword
                words = description.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        # Get surrounding context
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        phrase = ' '.join(words[start:end])
                        features.append(phrase)
                        break

        return ', '.join(features[:3]) if features else description[:100]
    
    # ✅ UPDATED: Add characters parameter
    async def generate_image(
        self, 
        request: ImageGenerationRequest, 
        model_name: str = "dream.safetensors",
        characters: List[Dict[str, Any]] = None  # ✅ ADD THIS
    ) -> bytes:
        """Generate comic panel image using ComfyUI with character consistency"""
        
        # ✅ UPDATED: Pass characters to build_prompt
        prompt = self.build_prompt(request.panel, characters)
        seed = request.seed if request.seed else int(asyncio.get_event_loop().time() * 1000) % 1000000
        
        workflow = {
            "1": {
                "inputs": {"ckpt_name": model_name},
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {"text": prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {"text": request.negative_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode"
            },
            "4": {
                "inputs": {
                    "width": request.width,
                    "height": request.height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "5": {
                "inputs": {
                    "seed": seed,
                    "steps": request.steps,
                    "cfg": request.cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                },
                "class_type": "KSampler"
            },
            "6": {
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
                "class_type": "VAEDecode"
            },
            "7": {
                "inputs": {
                    "filename_prefix": f"comic_panel_{request.panel.id}",
                    "images": ["6", 0]
                },
                "class_type": "SaveImage"
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Submit prompt
            response = await client.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow}
            )
            response.raise_for_status()
            result = response.json()
            prompt_id = result["prompt_id"]
            
            # Wait for completion
            image_data = await self._wait_for_completion(client, prompt_id, "7")
            
            return image_data
    
    async def _wait_for_completion(self, client: httpx.AsyncClient, prompt_id: str, save_node_id: str, max_attempts: int = 60) -> bytes:
        """Poll ComfyUI for completion and retrieve image"""
        
        for attempt in range(max_attempts):
            await asyncio.sleep(5)
            
            response = await client.get(f"{self.base_url}/history/{prompt_id}")
            history_data = response.json()
            
            if prompt_id in history_data:
                outputs = history_data[prompt_id].get("outputs", {})
                save_node = outputs.get(save_node_id, {})
                
                if "images" in save_node and len(save_node["images"]) > 0:
                    image_info = save_node["images"][0]
                    
                    # Download image
                    params = {"filename": image_info["filename"]}
                    if "subfolder" in image_info:
                        params["subfolder"] = image_info["subfolder"]
                    if "type" in image_info:
                        params["type"] = image_info["type"]
                    
                    img_response = await client.get(
                        f"{self.base_url}/view",
                        params=params
                    )
                    img_response.raise_for_status()
                    
                    return img_response.content
        
        raise TimeoutError(f"Image generation timeout for prompt {prompt_id}")

comfyui_service = ComfyUIService()