"""Cycle-safe directed dependency graph for evidence lifecycle propagation."""

from __future__ import annotations

from collections import deque

from app.evidence.models import DependencyReference


class DependencyCycleError(ValueError):
    """Raised when a new dependency would create a cycle."""


class EvidenceDependencyGraph:
    """Track upstream dependencies and downstream dependents in memory."""

    def __init__(self) -> None:
        self._dependencies: dict[str, set[str]] = {}
        self._dependents: dict[str, set[str]] = {}

    def add_node(self, item_id: str) -> None:
        self._dependencies.setdefault(item_id, set())
        self._dependents.setdefault(item_id, set())

    def add_dependency(
        self,
        dependent_id: str,
        dependency_id: str,
        relationship: str = "CREATED_FROM",
    ) -> DependencyReference:
        if dependent_id == dependency_id:
            raise DependencyCycleError("evidence cannot depend on itself")
        self.add_node(dependent_id)
        self.add_node(dependency_id)
        if dependent_id in self.list_dependencies(dependency_id, transitive=True):
            chain = " -> ".join(self.dependency_chain(dependency_id, dependent_id))
            raise DependencyCycleError(f"dependency cycle detected: {chain} -> {dependency_id}")
        self._dependencies[dependent_id].add(dependency_id)
        self._dependents[dependency_id].add(dependent_id)
        return DependencyReference(
            dependent_id=dependent_id,
            dependency_id=dependency_id,
            relationship=relationship,
        )

    def list_dependencies(self, item_id: str, *, transitive: bool = False) -> tuple[str, ...]:
        return self._walk(self._dependencies, item_id, transitive)

    def list_dependents(self, item_id: str, *, transitive: bool = False) -> tuple[str, ...]:
        return self._walk(self._dependents, item_id, transitive)

    def dependency_chain(self, start_id: str, target_id: str) -> tuple[str, ...]:
        """Return one upstream chain from start to target, inclusive, for debugging."""

        queue: deque[tuple[str, tuple[str, ...]]] = deque([(start_id, (start_id,))])
        visited: set[str] = set()
        while queue:
            node, path = queue.popleft()
            if node == target_id:
                return path
            if node in visited:
                continue
            visited.add(node)
            for dependency in sorted(self._dependencies.get(node, set())):
                queue.append((dependency, (*path, dependency)))
        return ()

    @staticmethod
    def _walk(graph: dict[str, set[str]], item_id: str, transitive: bool) -> tuple[str, ...]:
        direct = sorted(graph.get(item_id, set()))
        if not transitive:
            return tuple(direct)
        visited: set[str] = set()
        queue: deque[str] = deque(direct)
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(sorted(graph.get(node, set())))
        return tuple(sorted(visited))
