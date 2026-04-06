from typing import List


class EnvironmentName:
    def apply(self, parameters: dict, context: dict = None) -> bool:
        target_envs_str: str = parameters.get("envNames", "")
        target_envs: List[str] = [stripped for x in target_envs_str.split(",") if (stripped := x.strip())]

        if context and "envName" in context:
            return context["envName"] in target_envs

        return False
