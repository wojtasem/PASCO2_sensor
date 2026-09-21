from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Konfiguruje logowanie dla calej aplikacji.

    Wywolywane raz, w cli/main.py. Reszta kodu uzywa tylko
    logging.getLogger(__name__) - nigdy print().
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
