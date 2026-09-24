import os
import sys
import glob
import argparse
import time
from src.business.compression.compression import Compression
from src.business.compression.decompression import Decompression


def calculate_metrics(original_payload_str, compressed_size):
    """Computes the 3 most common compression metrics based solely on payload data."""
    uncompressed_size = len(original_payload_str.encode('ascii'))  # 1 byte per ASCII char
    
    if compressed_size == 0:
        return 1.0, 0.0, 8.0

    # 1. Compression Ratio
    compression_ratio = uncompressed_size / compressed_size
    
    # 2. Space Savings
    space_savings = (1.0 - (compressed_size / uncompressed_size)) * 100
    
    # 3. Bits Per Character (BPC)
    bits_per_character = (compressed_size * 8) / len(original_payload_str)
    
    return compression_ratio, space_savings, bits_per_character


def run_benchmarks(target_file=None):
    """Executes compression/decompression on message payloads and prints metrics."""
    benchmark_dir = os.path.join(os.path.dirname(__file__), "benchmarks")
    
    if target_file:
        if os.path.exists(target_file):
            files = [target_file]
        else:
            files = [os.path.join(benchmark_dir, target_file)]
    else:
        files = glob.glob(os.path.join(benchmark_dir, "*.txt"))

    if not files:
        print("❌ No benchmark files found matching target.")
        sys.exit(1)

    print(f"\n{'='*95}")
    print("⚡ BENCHMARK REPORT: PREDICTOR COMPRESSION (PAYLOAD ONLY)")
    print(f"{'='*95}")
    print(f"{'Filename':<25} | {'Orig (B)':<8} | {'Comp (B)':<8} | {'Ratio':<6} | {'Savings':<8} | {'BPC':<5} ")
    # | {'Time (ms)':<8}
    print(f"{'-'*95}")

    for file_path in files:
        if not os.path.exists(file_path):
            print(f"Skipping {os.path.basename(file_path)}: File not found.")
            continue
            
        with open(file_path, "r", encoding="ascii") as f:
            lines = f.readlines()

        # One Compression/Decompression pair per speaker: in the real app, a
        # speaker's outgoing messages are compressed by their own Node's Client
        # and decompressed by the peer's Node's Server, so those two tables stay
        # in lockstep with each other but never see the other speaker's stream.
        speaker_codecs = {}

        total_payload_uncompressed = ""
        total_execution_time_ms = 0.0
        total_compressed_size = 0
        lossless_validation_passed = True

        # Process conversation line-by-line to isolate Speaker from Message
        for line in lines:
            line = line.strip()
            if not line or ": " not in line:
                continue

            # Split into Speaker ("Alice") and Message ("Hey! How'd ur day go?...")
            speaker, payload = line.split(": ", 1)

            if speaker not in speaker_codecs:
                speaker_codecs[speaker] = (Compression(), Decompression())
            compressor, decompressor = speaker_codecs[speaker]

            total_payload_uncompressed += payload

            # Benchmark the compression of the payload only
            start_time = time.perf_counter()
            compressed_payload = compressor.payload_compression(payload)
            end_time = time.perf_counter()

            total_execution_time_ms += (end_time - start_time) * 1000
            total_compressed_size += len(compressed_payload)

            # Verify fidelity immediately via decompression
            decompressed_payload = decompressor.payload_decompression(compressed_payload)
            if decompressed_payload != payload:
                lossless_validation_passed = False
                print(f"❌ CRITICAL ERROR: Lossless validation failed for line: '{line}'")
                break

        if not lossless_validation_passed:
            continue

        # Metric evaluations based purely on the message contents
        # total_compressed_size is safely passed as an int
        ratio, savings, bpc = calculate_metrics(total_payload_uncompressed, total_compressed_size)
        
        filename = os.path.basename(file_path)
        print(f"{filename:<36} | {len(total_payload_uncompressed):<6} | {total_compressed_size:<6} | {ratio:.2f}x   | {savings:.1f}%    | {bpc:.2f}")
        # | {total_execution_time_ms:.2f}
        
    print(f"{'='*95}\n")

def main():
    # Create the main parser
    parser = argparse.ArgumentParser(description="Main Command")

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command")

    # Define a subcommand 'log'
    benchmark_parser = subparsers.add_parser(
        "benchmark", help='Run metric evaluations from "benchmarks" subfolder.'
    )
    benchmark_parser.add_argument("text", type=str, nargs="*", help="Text to log")

    benchmark_parser.add_argument(
        "--test-file",
        nargs="?",
        default=None,
        help="Optional specific corpus filename or path inside benchmarks/ directory.",
    )

    # Parse the arguments
    args = parser.parse_args()
    benchmark_args = benchmark_parser.parse_args()

    # Example function to handle the log command
    if args.command == "benchmark":
        run_benchmarks(benchmark_args.test_file)


if __name__ == "__main__":
    main()
