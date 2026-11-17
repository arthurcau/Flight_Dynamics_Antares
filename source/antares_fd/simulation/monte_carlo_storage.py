"""Bounded storage for the trajectories actually used by campaign plots."""

import random
from threading import Lock

from multiprocess.managers import SyncManager


class TrajectoryStore:
    """Keep four endpoint extrema and a uniform reservoir of five full paths.

    All trajectory points retain their original precision. Only paths that are
    not needed by the plots are released. The private RNG never consumes the
    simulation's random stream. Methods are locked because manager requests
    from different workers run on different server threads.
    """

    def __init__(self, seed=42):
        """Inicialize o armazenamento limitado de trajetórias de diagnóstico.

        Define capacidades de extremos e amostras, listas internas e contadores.
        A retenção é independente do número total de casos executados.
        """
        self._rng = random.Random(seed)
        self._lock = Lock()
        self._count = 0
        self._extremes = {}
        self._sample = []

    def append(self, trajectory):
        """Incorpore uma trajetória mantendo apenas extremos e amostras limitadas.

        Atualiza o contador de casos vistos e seleciona registros para visualização
        conforme a capacidade. Modifica o armazenamento; não altera o voo original.
        """
        x, y = trajectory["x"][-1], trajectory["y"][-1]
        with self._lock:
            self._count += 1
            entry = (self._count, trajectory)
            for name, score in (("east", x), ("west", -x),
                                ("north", y), ("south", -y)):
                previous = self._extremes.get(name)
                if previous is None or score > previous[0]:
                    self._extremes[name] = (score, entry)

            # Reservoir sampling: every completed path has probability 5/N of
            # being in the KML sample, regardless of completion order.
            if len(self._sample) < 5:
                self._sample.append(entry)
            else:
                slot = self._rng.randrange(self._count)
                if slot < 5:
                    self._sample[slot] = entry

    def snapshot(self):
        """Retorne uma cópia compacta das trajetórias retidas e dos contadores.

        Agrupa extremos e amostras em um dicionário serializável para consumo
        fora do processo gerenciador. Não entrega o objeto completo de cada Flight.
        """
        with self._lock:
            unique = dict(entry for _, entry in self._extremes.values())
            unique.update(self._sample)
            return {
                "trajectories": list(unique.values()),
                "samples": [path for _, path in self._sample],
                "seen": self._count,
            }


class CampaignManager(SyncManager):
    """Use the same multiprocess backend as RocketPy, including on Windows."""


CampaignManager.register("TrajectoryStore", TrajectoryStore)
