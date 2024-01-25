from __future__ import annotations

from dataclasses import dataclass, field

from .transform import ImageTransformer
from ..transformers import TransformerGroup, GrayFilter


@dataclass
class TransformBuilder:
    _transformers: list[ImageTransformer] = field(default_factory=list)

    def transformer(self, transformer: ImageTransformer) -> TransformBuilder:
        """Adds an transformer to the builder instance.
        
        Args:
            transformer : ImageTransformer
                Instance of an Image Tranformer Object to be added

        Returns:
            TransformBuilder instance
        """
        self._transformers.append(transformer)
        return self

    def gray(self) -> TransformBuilder:
        transformer = GrayFilter()
        return self.transformer(transformer)

    def build(self) -> ImageTransformer:
        return TransformerGroup(self._transformers)