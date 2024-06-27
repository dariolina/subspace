from subspace_model.units import *

U32_RANGE = 2**32
U128_RANGE = 2**128
MIB_IN_BYTES = 1_048_576
GIB_IN_BYTES = 1_073_741_824
PB_IN_BYTES = 1_125_899_906_842_624
DAY_TO_SECONDS = 24 * 60 * 60

# Subspace Constants
MAX_CREDIT_ISSUANCE: Credits = 1_000_000_000
LIQUID_AT_LAUNCH: Credits = MAX_CREDIT_ISSUANCE * 0.155
ISSUANCE_FOR_FARMERS: Credits = MAX_CREDIT_ISSUANCE * 0.3557
KZG_COMMITMENT: Bytes = 32  # As per Subnomicon
WITNESS: Bytes = 48  # As per Subnomicon
CHUNK_SIZE: Bytes = 48  # As per Subnomicon
ARCHIVAL_DEPTH: Blocks = 100  # As per Subnomicon
BLOCK_TIME: Seconds = 6  # As per Subnomicon. Approximate value.
RAW_RECORD_IN_CHUNKS: Chunk = 2**15  # As per Subnomicon
PIECE_SIZE: Bytes = (
    RAW_RECORD_IN_CHUNKS * CHUNK_SIZE + KZG_COMMITMENT + WITNESS
)  # As per Subnomicon
SECTOR_IN_PIECES: Piece = 1_000  # As per Subnomicon
SECTOR_SIZE = SECTOR_IN_PIECES * PIECE_SIZE  # ~= 1 MiB
SEGMENT_SIZE: Bytes = 128 * MIB_IN_BYTES  # As per discussions
SEGMENT_HISTORY_SIZE: Bytes = SEGMENT_SIZE * 2  # As per discussions
SHANNON_IN_CREDITS: Credits = 1e-18
CREDIT_IN_SHANNONS: Shannon = 1e18

# Weight References
WEIGHT_REF_TIME_PER_SECOND: Picoseconds = 10e12
WEIGHT_REF_TIME_PER_MILLI: Picoseconds = 10e6
WEIGHT_REF_TIME_PER_MICRO: Picoseconds = 10e3
WEIGHT_REF_TIME_PER_NANO: Picoseconds = 10
BLOCK_WEIGHT_FOR_2_SEC: Picoseconds = 2 * WEIGHT_REF_TIME_PER_SECOND


# Convenience Constants
BLOCKS_PER_DAY: Blocks = DAY_TO_SECONDS / BLOCK_TIME
BLOCKS_PER_YEAR: Blocks = BLOCKS_PER_DAY * 365
BLOCKS_PER_MONTH: Blocks = BLOCKS_PER_YEAR / 12
BLOCKS_PER_WEEK: Blocks = BLOCKS_PER_DAY * 7
