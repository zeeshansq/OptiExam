import secrets
import hashlib

def generate_secure_token(length: int = 32) -> str:
    """Generates a cryptographically secure hex token for exam resume or verification."""
    return secrets.token_hex(length)

def generate_candidate_seed(participant_id: int, exam_id: int) -> int:
    """
    Computes a deterministic integer seed from participant and exam IDs
    for consistent question and option shuffling across reconnects.
    """
    raw_key = f"{participant_id}:{exam_id}".encode('utf-8')
    digest = hashlib.sha256(raw_key).hexdigest()
    return int(digest[:8], 16)
