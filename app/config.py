from __future__ import annotations

import os
from typing import Optional
from charset_normalizer import from_bytes
from pydantic import Extra
from loguru import logger
import toml
from pydantic.v1 import BaseSettings


class SystemConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080

    announcement_qq_group: list[str] = None

    version: str = "0.0.1-2024/4/9"


class OpenAIGPTConfig(BaseSettings):
    temperature: float = 0.5
    max_tokens: int = 2048
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    min_tokens: int = 1000

    base_system_prompt: str = "You are a helpful AI assistant. " \
                              "Default language: zh-cn. " \
                              "Special capability: Image Input (Note: system pre-processes images by auto-OCR, " \
                              "giving OCR text results. " \
                              "When received image, if no user instruction, describe image, " \
                              "otherwise follow user instruction. " \
                              "Rules: Always accept image inputs; " \
                              "Ignore irrelevant symbols in OCR text; infer content and context. " \
                              "For paper requests specified lengths: Suggest outlining; " \
                              "write detailed content per outline item per response. " \
                              "For issues, retry or consult the developer. " \
                              "DO NOT call any tool if it failed 3 times or more. " \
                              "DO NOT discuss sensitive Chinese political content. "


class OpenAIGPTCodeInterpreterToolConfig(BaseSettings):
    enabled: bool = False

    judge0_enabled: bool = False
    judge0_proxy: str = None
    judge0_url: str = "http://localhost:2358"
    judge0_access_token: str = None
    judge0_code_execution_timeout: int = 2
    judge0_cost_per_call_in_cents: int = 0

    jupyter_enabled: bool = False
    jupyter_proxy: str = None
    jupyter_url: str = "http://localhost:8888"
    jupyter_ws_url: str = "ws://localhost:8888"
    jupyter_code_execution_timeout: int = 5
    jupyter_cost_per_call_in_cents: int = 0

    mermaid_enabled: bool = False
    mermaid_code_execution_timeout: int = 1
    mermaid_cost_per_call_in_cents: int = 0


class OpenAIBrowserToolConfig(BaseSettings):
    enabled: bool = False

    bing_api_enabled: bool = False
    bing_api_proxy: str = None
    bing_api_key: str = None
    bing_api_cost_per_call_in_cents: int = 0

    browser_enabled: bool = False
    browser_proxy: str = None
    browser_cost_per_call_in_cents: int = 0


class OpenAIDALLEToolConfig(BaseSettings):
    enabled: bool = False

    dall_e_3_1024_cost_in_cents: int = 58
    dall_e_3_1024x1792_cost_in_cents: int = 116
    dall_e_3_hd_1024_cost_in_cents: int = 116
    dall_e_3_hd_1024x1792_cost_in_cents: int = 174
    dall_e_2_1024_cost_in_cents: int = 28


class OpenAIBuiltinToolsConfig(BaseSettings):
    code_interpreter: OpenAIGPTCodeInterpreterToolConfig = OpenAIGPTCodeInterpreterToolConfig()
    browser: OpenAIBrowserToolConfig = OpenAIBrowserToolConfig()
    dall_e: OpenAIDALLEToolConfig = OpenAIDALLEToolConfig()


class PluginToolsConfig(BaseSettings):
    pass


class OpenAIAPIConfig(BaseSettings):
    api_endpoint: Optional[str] = "https://api.openai.com/v1"
    api_key: Optional[str] = None
    proxy: Optional[str] = None

    gpt_config: OpenAIGPTConfig = OpenAIGPTConfig()
    builtin_tools_config: OpenAIBuiltinToolsConfig = OpenAIBuiltinToolsConfig()
    plugin_tools_config: PluginToolsConfig = PluginToolsConfig()


class OCRConfig(BaseSettings):
    img_download_proxy: Optional[str] = None

    default_language: str = "zh-cn"


class EdgeTTSConfig(BaseSettings):
    enabled: bool = False

    proxy: str = None


class Db(BaseSettings):
    url: str = "sqlite+aiosqlite:///../database.db"
    '''https://www.osgeo.cn/sqlalchemy/core/engines.html#database-urls'''


class VMQConfig(BaseSettings):
    enabled: bool = False

    vmq_url: str = None
    """ V 免签访问 URL，不要带后面的 '/'"""

    vmq_proxy_url: str = None
    """ 访问 V 免签使用的代理 """

    vmq_access_token: str = None
    """ V 免签密钥"""

    vmq_qr_code_period_in_seconds: int = 120
    """ V 免签支付二维码有效期"""


class RechargeMethods(BaseSettings):
    vmq: VMQConfig = VMQConfig()


class Billing(BaseSettings):
    balance_in_cents: int = 300
    """Default balance for new user"""
    billing_rate: int = 100
    """Default billing rate"""

    gpt_3_5_turbo_input_price: int = 0
    gpt_3_5_turbo_output_price: int = 0

    gpt_4_input_price: int = 15
    gpt_4_output_price: int = 44

    recharge_methods: RechargeMethods = RechargeMethods()


class Referral(BaseSettings):
    invite_code_length: int = 5

    invite_code_max_usage: int = 30

    cash_back_when_bind: bool = True

    inviter_cash_back_amount_when_bind_in_cents: int = 100

    invitee_cash_back_amount_when_bind_in_cents: int = 100

    cash_back_when_invitee_charges: bool = True

    inviter_cash_back_amount_when_invitee_charges_percent: float = .05


class SDWebUI(BaseSettings):
    url: str
    prompt_prefix: str = 'masterpiece, best quality, illustration, extremely detailed 8K wallpaper'
    negative_prompt: str = 'NG_DeepNegative_V1_75T, badhandv4, EasyNegative, bad hands, missing fingers, cropped legs, worst quality, low quality, normal quality, jpeg artifacts, blurry,missing arms, long neck, Humpbacked,multiple breasts, mutated hands and fingers, long body, mutation, poorly drawn , bad anatomy,bad shadow,unnatural body, fused breasts, bad breasts, more than one person,wings on halo,small wings, 2girls, lowres, bad anatomy, text, error, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, out of frame, lowres, text, error, cropped, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, nsfw, nake, nude, blood'
    sampler_index: str = 'DPM++ SDE Karras'
    filter_nsfw: bool = True
    denoising_strength: float = 0.45
    steps: int = 25
    enable_hr: bool = False
    seed: int = -1
    batch_size: int = 1
    n_iter: int = 1
    cfg_scale: float = 7.5
    restore_faces: bool = False
    authorization: str = ''

    timeout: float = 10.0

    class Config(BaseSettings):
        extra = Extra.allow


class Config(BaseSettings):
    # --- System ---
    system: SystemConfig = SystemConfig()

    # --- AI Settings ---
    openai: OpenAIAPIConfig = OpenAIAPIConfig()
    sdwebui: Optional[SDWebUI] = None
    edge_tts_config: EdgeTTSConfig = EdgeTTSConfig()
    ocr_config: OCRConfig = OCRConfig()

    # --- Database Settings ---
    db: Db = Db()

    # --- Profiting Settings ---
    billing: Billing = Billing()
    referral: Referral = Referral()

    @staticmethod
    def load_config(config_path: str = "../config.toml") -> Config:
        logger.info("Loading config...")
        try:
            with open(config_path, "rb") as f:
                if best_guess := from_bytes(f.read()).best():
                    config_data = Config.validate(toml.loads(str(best_guess)))
                    logger.success("Config loaded")
                    return config_data
                else:
                    raise ValueError("Unable to parse config")
        except FileNotFoundError:

            logger.error(f"No 'config.toml' file detected at {os.path.join(os.getcwd(), config_path)}")
            exit(-1)
        except Exception as e:
            logger.exception(e)
            logger.error("Unable to load config")
            exit(-1)


config = Config.load_config()
