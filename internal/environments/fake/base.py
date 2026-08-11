from abc import ABC, abstractmethod
from typing import List, Dict

# ileride döngüsel bağımlılık(circular import) olmasın diye VFS'nin
# tipini sadece string olarak veriyoruz.
# Veya 'Any' de kullanabiliriz

from typing import Any

class BaseCommand(ABC):
    """
    Sanal işletim sisteminde tüm komutlar (ls, cat, whoami vb.)
    türemek zorunda olduğu şablon sınıf.
    """

    @abstractmethod
    def execute(self, args: List[str], vfs: Any, env: Dict[str, str]) -> str:
        """
        Her komut bu methodu içermek zorundadır!
        :param args: Kullanıcının yazdığı komur parametreleri (Örn: ['-la', ''/tmp])
        :param vfs: Sanal Dosya Sistemi(VirtualFileSystem) objesi
        :param: Hacker'ın ekranında basaılacak olan string(çıktı)
        """
        pass

    @property
    def help_text(self) -> str:
            """
            Komut bulanamdığında veya --help yazıldığında çıkacak yardım metni.
            """
            return "Bu komut için yardım metni bulunmuyor.\n"