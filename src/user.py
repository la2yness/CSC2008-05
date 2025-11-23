"""
사용자 프로필 및 제약조건 처리
"""

from typing import Dict, Optional


class UserProfile:

    def __init__(self, age: int, height: float, name: str = "User"):
        """
        Args:
            age: 나이 (세)
            height: 키 (cm)
            name: 사용자 이름
        """
        self.age = age
        self.height = height
        self.name = name

    def to_dict(self) -> Dict:
        return {
            "age": self.age,
            "height": self.height,
            "name": self.name
        }

    def __repr__(self):
        return f"UserProfile(name={self.name}, age={self.age}, height={self.height}cm)"


def create_user_profile(age: int, height: float, name: str = "User") -> Dict:
    """
    사용자 프로필 생성 헬퍼 함수

    Args:
        age: 나이 (세)
        height: 키 (cm)
        name: 사용자 이름

    Returns:
        프로필 딕셔너리
    """
    return {
        "age": age,
        "height": height,
        "name": name
    }
