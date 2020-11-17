#!/usr/bin/env python

from abc import abstractmethod
from typing import Tuple, Dict

from utils.data_types import TechnologyId


class Technology:
    def __init__(self,
                 id: TechnologyId,
                 name: str,
                 required: Tuple[TechnologyId] = (),
                 allow: Tuple[TechnologyId] = (),
                 difficulty: float = 100.0):
        self.id = id
        self.name = name
        self.description = None
        self.required = required
        self.allow = allow
        self.difficulty = difficulty

    def unlocked(self, researcher) -> bool:
        return all(tech_id in researcher.known_technologies for tech_id in self.required)

    @abstractmethod
    def gain_technology_effects(self, researcher):
        raise NotImplementedError

