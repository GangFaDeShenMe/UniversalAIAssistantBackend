import os
import tempfile
import toml
from app.config import Config
from loguru import logger

logger.remove()  # 移除默认的logger，以避免在测试中打印日志


def create_temp_config_file(config_data: dict):
    """
    创建一个临时的 config.toml 文件，并写入测试数据。
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".toml")
    with open(temp_file.name, 'w') as file:
        toml.dump(config_data, file)
    return temp_file.name


def test_load_config():
    # 定义一些测试数据
    test_data = {
        "system": {
            "host": "127.0.0.1",
            "port": 8000,
            "announcement_qq_group": ["12345", "67890"],
        },
        "openai": {
            "api_key": "1234asdf",
            "gpt_config": {
                "temperature": 0.9,
                "max_tokens": 456
            }
        }
    }

    # 创建临时的 config.toml 文件
    temp_config_path = create_temp_config_file(test_data)

    # 修改 Config 类中的方法，以使用临时的 config.toml 文件路径
    original_load_config_method = Config.load_config

    def temp_load_config():
        nonlocal temp_config_path
        return original_load_config_method(temp_config_path)

    Config.load_config = staticmethod(temp_load_config)

    # 加载配置并进行断言测试
    loaded_config = Config.load_config()
    assert loaded_config.system.host == "127.0.0.1"
    assert loaded_config.system.port == 8000
    assert loaded_config.system.announcement_qq_group == ["12345", "67890"]
    assert loaded_config.openai.api_key == "1234asdf"
    assert loaded_config.openai.gpt_config.temperature == 0.9
    assert loaded_config.openai.gpt_config.max_tokens == 456

    # 清理：删除临时文件，并恢复 Config 类的原始方法
    os.remove(temp_config_path)
    Config.load_config = original_load_config_method
