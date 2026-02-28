"""
Configuration Validator Module

Validates and auto-corrects configuration values to ensure
proper operation of translation and polishing tasks.
"""

import os
import sys
from typing import Dict, Any, List, Tuple, Optional, Union
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.is_valid = True
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.corrections: Dict[str, Any] = {}

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def add_error(self, message: str):
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_correction(self, key: str, old_value: Any, new_value: Any):
        """Record a correction made."""
        self.corrections[key] = {
            "old": old_value,
            "new": new_value
        }

    def get_summary(self) -> str:
        """Get a summary of validation results."""
        parts = []
        if self.is_valid:
            parts.append("✅ Configuration is valid")
        else:
            parts.append("❌ Configuration has errors")

        if self.warnings:
            parts.append(f"⚠️ {len(self.warnings)} warnings")

        if self.corrections:
            parts.append(f"🔧 {len(self.corrections)} corrections made")

        return ", ".join(parts)


class ConfigValidator:
    """
    Validates and corrects configuration values.

    Features:
    - Language code validation and normalization
    - Bilingual output configuration validation
    - Platform configuration validation
    - API settings validation
    - File path validation
    """

    def __init__(self, logger=None):
        """
        Initialize validator.

        Args:
            logger: Optional logger instance for output
        """
        self.logger = logger
        self._language_mapper = None

    def _log(self, message: str, level: str = "info"):
        """Log a message if logger is available."""
        if self.logger:
            if level == "info":
                self.logger.info(message)
            elif level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)

    def _get_language_mapper(self):
        """Lazy load language mapper."""
        if self._language_mapper is None:
            try:
                from Tools.WebServer.language_mapper import (
                    normalize_language_input,
                    validate_language_code,
                    map_display_name_to_code
                )
                self._language_mapper = {
                    "normalize": normalize_language_input,
                    "validate": validate_language_code,
                    "map_display": map_display_name_to_code
                }
            except ImportError:
                # Fallback to basic validation if language_mapper not available
                self._language_mapper = {
                    "normalize": lambda x: x if x and "_" in x else "auto",
                    "validate": lambda x: x in ["auto", "english", "chinese_simplified",
                                                "chinese_traditional", "japanese"],
                    "map_display": lambda x: x
                }
        return self._language_mapper

    def validate_config(self, config: Any) -> ValidationResult:
        """
        Validate all aspects of configuration.

        Args:
            config: TaskConfig instance to validate

        Returns:
            ValidationResult with details
        """
        result = ValidationResult()

        # Validate language settings
        self._validate_languages(config, result)

        # Validate bilingual output settings
        self._validate_bilingual_config(config, result)

        # Validate platform configuration
        self._validate_platform_config(config, result)

        # Validate API settings
        self._validate_api_settings(config, result)

        # Validate file paths
        self._validate_file_paths(config, result)

        # Validate numeric settings
        self._validate_numeric_settings(config, result)

        return result

    def _validate_languages(self, config: Any, result: ValidationResult):
        """Validate and correct language settings."""
        mapper = self._get_language_mapper()

        # Validate source_language
        source_lang = getattr(config, "source_language", "auto")
        if source_lang:
            normalized_source = mapper["normalize"](source_lang)
            if normalized_source != source_lang:
                result.add_correction(
                    "source_language",
                    source_lang,
                    normalized_source
                )
                config.source_language = normalized_source
                result.add_warning(
                    f"Source language normalized: '{source_lang}' → '{normalized_source}'"
                )

            # Validate the normalized code
            if not mapper["validate"](normalized_source):
                result.add_error(
                    f"Invalid source language code: '{source_lang}'"
                )

        # Validate target_language
        target_lang = getattr(config, "target_language", "chinese_simplified")
        if target_lang:
            normalized_target = mapper["normalize"](target_lang)
            if normalized_target != target_lang:
                result.add_correction(
                    "target_language",
                    target_lang,
                    normalized_target
                )
                config.target_language = normalized_target
                result.add_warning(
                    f"Target language normalized: '{target_lang}' → '{normalized_target}'"
                )

            # Target language cannot be auto
            if normalized_target == "auto":
                result.add_error(
                    "Target language cannot be 'auto', please specify a valid language"
                )

            # Validate the normalized code
            if not mapper["validate"](normalized_target):
                result.add_error(
                    f"Invalid target language code: '{target_lang}'"
                )

    def _validate_bilingual_config(self, config: Any, result: ValidationResult):
        """Validate bilingual output configuration."""
        bilingual_enabled = getattr(config, "enable_bilingual_output", False)

        if not isinstance(bilingual_enabled, bool):
            result.add_error(
                f"enable_bilingual_output must be boolean, got {type(bilingual_enabled).__name__}"
            )
            config.enable_bilingual_output = False

        # Check bilingual_text_order
        text_order = getattr(config, "bilingual_text_order", "translation_first")
        valid_orders = ["translation_first", "original_first"]

        if text_order not in valid_orders:
            result.add_warning(
                f"Invalid bilingual_text_order '{text_order}', must be one of {valid_orders}"
            )
            config.bilingual_text_order = "translation_first"
            result.add_correction(
                "bilingual_text_order",
                text_order,
                "translation_first"
            )

        # Log bilingual output status
        if bilingual_enabled:
            self._log(
                f"✅ Bilingual output enabled (order: {config.bilingual_text_order})",
                "info"
            )
        else:
            self._log(
                "ℹ️ Bilingual output disabled - only _translated.txt will be generated",
                "info"
            )

    def _validate_platform_config(self, config: Any, result: ValidationResult):
        """Validate platform configuration."""
        platforms = getattr(config, "platforms", {})
        target_platform = getattr(config, "target_platform", "")

        if not target_platform:
            result.add_error("No target_platform specified")
            return

        if target_platform not in platforms:
            result.add_error(
                f"Target platform '{target_platform}' not found in platforms config. "
                f"Available platforms: {list(platforms.keys())}"
            )
            return

        # Validate platform configuration
        platform_conf = platforms[target_platform]
        required_fields = ["api_url", "api_format", "model"]

        for field in required_fields:
            if field not in platform_conf or not platform_conf[field]:
                result.add_error(
                    f"Platform '{target_platform}' missing required field: '{field}'"
                )

    def _validate_api_settings(self, config: Any, result: ValidationResult):
        """Validate API settings."""
        api_settings = getattr(config, "api_settings", {})

        if not api_settings:
            result.add_error("No api_settings configured")
            return

        # Check for required API settings based on mode
        translate_api = api_settings.get("translate")
        polish_api = api_settings.get("polish")

        if not translate_api:
            result.add_warning(
                "No 'translate' API specified in api_settings"
            )

        if not polish_api:
            result.add_warning(
                "No 'polish' API specified in api_settings"
            )

    def _validate_file_paths(self, config: Any, result: ValidationResult):
        """Validate file paths."""
        # Check input path
        input_path = getattr(config, "label_input_path", "")

        if input_path and not os.path.exists(input_path):
            result.add_warning(
                f"Input path does not exist: '{input_path}'"
            )

        # Validate output paths if they exist
        output_path = getattr(config, "translated_output_path", "")
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    result.add_correction(
                        "translated_output_path",
                        output_path,
                        f"Created directory: {output_dir}"
                    )
                except OSError as e:
                    result.add_error(
                        f"Cannot create output directory '{output_dir}': {e}"
                    )

    def _validate_numeric_settings(self, config: Any, result: ValidationResult):
        """Validate numeric settings."""
        # Validate thread counts
        user_threads = getattr(config, "user_thread_counts", 0)
        if user_threads < 0:
            result.add_warning(
                f"user_thread_counts cannot be negative (got {user_threads}), setting to 0"
            )
            config.user_thread_counts = 0

        # Validate retry count
        retry_count = getattr(config, "retry_count", 3)
        if retry_count < 0:
            result.add_warning(
                f"retry_count cannot be negative (got {retry_count}), setting to 3"
            )
            config.retry_count = 3

        # Validate round limit
        round_limit = getattr(config, "round_limit", 3)
        if round_limit < 0:
            result.add_warning(
                f"round_limit cannot be negative (got {round_limit}), setting to 0"
            )
            config.round_limit = 0

        # Validate timeout
        timeout = getattr(config, "request_timeout", 60)
        if timeout <= 0:
            result.add_warning(
                f"request_timeout must be positive (got {timeout}), setting to 60"
            )
            config.request_timeout = 60


def validate_and_correct_config(config: Any, logger=None) -> ValidationResult:
    """
    Convenience function to validate and correct configuration.

    Args:
        config: TaskConfig instance to validate
        logger: Optional logger instance

    Returns:
        ValidationResult with details
    """
    validator = ConfigValidator(logger)
    return validator.validate_config(config)
