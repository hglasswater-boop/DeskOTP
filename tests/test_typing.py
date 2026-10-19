import pytest
from deskotp.typing import type_into_foreground

@pytest.mark.parametrize("text", ["", "12345", "1234567", "123456789", "12345a", "12\n456", "１２３４５６"])
def test_never_type_non_otp_input(text):
    with pytest.raises(ValueError):
        type_into_foreground(text)
