"""List functions generators"""

from dataclasses import dataclass
from random import Random
from typing import Any, Callable, Optional

from reasoning_gym.factory import ProceduralDataset, register_dataset


@dataclass
class ListFunctionsDatasetConfig:
    """Configuration for List function generators."""

    seed: Optional[int] = None
    size: int = 500

    def validate(self) -> None:
        """Validate configuration parameters"""
        assert self.size > 0, "size must be positive"


tasks = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
]


class ListFunctionsDataset(ProceduralDataset):

    def __init__(self, config: ListFunctionsDatasetConfig):
        super().__init__(config, config.seed, config.size)
        self._generators: dict[int, Callable[[Random, float], dict[str, Any]]] = None  # initially None, lazy loading
        self.task_indices = Random(self.seed).choices(tasks, k=self.size)
        self.prompt_template = """You are an expert at inductive reasoning. Generate an output corresponding to the given input.
The output is generated by applying the same rule that maps input to output for the examples provided. Your answer should be a list of element/elements
Examples:
{examples}

Input: {input}
Output:
"""

    @property
    def generators(self) -> dict[int, Callable[[Random, float], dict[str, Any]]]:
        """Lazy load generators only when first accessed"""
        if self._generators is None:
            self._generators = self._load_generators()
        return self._generators

    def _load_generators(self):
        """
        Generates mapper from task identifiers (keys) to example generator functions
        """
        from . import generators

        def strip_prefix(s: str, prefix: str) -> str:
            return s[len(prefix) :]

        prefix = "generate_"
        gs = {}
        for n in dir(generators):
            if n.startswith(prefix):
                gs[int(strip_prefix(n, prefix))] = getattr(generators, n)
        return gs

    def __getitem__(self, idx: int) -> dict:
        """Generate a single induction-based list function dataset"""
        rng = Random(self.seed + idx)
        generator_idx = self.task_indices[idx]
        generator = self.generators[generator_idx]
        examples = generator(rng)
        entry = examples.popitem()
        input = entry[0]
        output = entry[1]
        formatted_examples = ""
        for index, key in enumerate(examples):
            formatted_examples += f"""Input {index + 1}: {key}
Output {index + 1}: {examples[key]}
"""
        question = self.prompt_template.format(examples=formatted_examples, input=input)
        return {"question": question, "answer": output, "metadata": {}}


register_dataset("list_functions", ListFunctionsDataset, ListFunctionsDatasetConfig)
