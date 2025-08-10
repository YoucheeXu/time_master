# !/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import TypeVar
from typing import Mapping, Iterator


KT = TypeVar('KT')
VT = TypeVar('VT')


class BidirectionalDict(Mapping[KT, VT]):
    def __init__(self, dict_: dict[KT, VT]):
        # 初始化两个字典，一个用于正向查找，一个用于反向查找
        self._forward: dict[KT, VT] = {}
        self._backward: dict[VT, KT] = {}

        for key, value in dict_.items():
            self._forward[key] = value
            # 添加反向查找
            self._backward[value] = key        

    @property
    def forward(self):
        return self._forward

    @property
    def backward(self):
        return self._backward

    def __del__(self):
        self._forward.clear()
        self._backward.clear()

    def __getitem__(self, k: KT) -> VT:
        return self.key_to_value(k)

    def __iter__(self) -> Iterator[KT]:
        pass

    def __len__(self) -> int:
        return len(self._forward)

    def add(self, key: KT, value: VT):
        # 添加正向查找
        self._forward[key] = value
        # 添加反向查找
        self._backward[value] = key

    def key_to_value(self, key: KT, dftval: VT | None = None) -> VT:
        """ 通过键获取值
        Args:
            key (): key.
            dftval (): default value.

        Returns:
            VT: return value.
        """
        return self._forward.get(key, dftval)  # 如果找不到键，返回 None

    def value_to_key(self, value: VT, dftkey: KT | None = None) -> KT:
        """ 通过值获取键
        Args:
            value (): value.
            dftkey (): default key.

        Returns:
            KT: return key
        """
        return self._backward.get(value, dftkey)  # 如果找不到值，返回 None

    def remove(self, key: KT):
        """ 通过键删除
        """
        value = self._forward.pop(key, None)  # 删除并获取值
        if value:
            # 反向删除
            _ = self._backward.pop(value, None)
