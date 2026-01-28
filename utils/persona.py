import yaml
import os
from typing import Dict, Any, Optional
from context.manager import context_manager

class PersonaLoader:
    def __init__(self, personas_dir: str = "personas"):
        # Resolve absolute path relative to project root usually, but here likely cwd
        self.personas_dir = personas_dir

    def load_persona(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """
        Loads a persona YAML file. Checks Redis cache first.
        Args:
            persona_name: filename without extension (e.g. 'default')
        """
        # 1. Try Redis Cache
        try:
            cached = context_manager.get_persona_template(persona_name)
            if cached:
                # print(f"✨ Loaded persona '{persona_name}' from Redis")
                return cached
        except Exception:
            pass # Fallback to disk if Redis fails (though context_manager usually handles it)

        # 2. Fallback to Disk
        file_path = os.path.join(self.personas_dir, f"{persona_name}.yaml")
        if not os.path.exists(file_path):
            print(f"⚠️ Persona file not found: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
                # 3. Save to Redis
                if data:
                    try:
                        context_manager.set_persona_template(persona_name, data)
                    except Exception as e:
                        print(f"⚠️ Failed to cache persona to Redis: {e}")
                
                return data
        except Exception as e:
            print(f"❌ Error loading persona {persona_name}: {e}")
            return None

    def format_persona_prompt(self, persona_data: Dict[str, Any]) -> str:
        """
        Converts the persona dict into a System Prompt string.
        """
        name = persona_data.get("name", "Nakari")
        bio = persona_data.get("bio", "")
        traits = ", ".join(persona_data.get("traits", []))
        tone = persona_data.get("tone", "")
        beliefs = "\n".join([f"- {b}" for b in persona_data.get("core_beliefs", [])])

        prompt = (
            f"You are {name}.\n\n"
            f"**Bio**:\n{bio}\n\n"
            f"**Personality Traits**: {traits}\n"
            f"**Tone**: {tone}\n\n"
            f"**Core Beliefs (These guide your judgment)**:\n{beliefs}\n\n"
        )
        return prompt

# Global instance
persona_loader = PersonaLoader()
