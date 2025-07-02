import os 
import argparse 
import settings 

parser = argparse.ArgumentParser(description="Preprocess documents for RAGx") 

# Arguments 
parser.add_argument(
    "--data_dir",
    type=str,
    default="./data",
    help="Directory containing the documents to preprocess.",
) 
parser.add_argument(
    "--strategy",
    type=str,
    default="naive",
    help="Preprocessing strategy to use."
)

args = parser.parse_args() 

def main():
    """Main function to run the preprocessing."""
    print(f"Preprocessing documents in {args.data_dir} using strategy '{args.strategy}'...")

    # Import the preprocessing module dynamically based on the strategy
    try:
        preprocess_module = __import__(f"preprocess.preprocess_{args.strategy}", fromlist=["preprocess"])
        preprocess_module.preprocess(args.data_dir)
    except ImportError as e:
        raise ImportError(f"Preprocessing strategy '{args.strategy}' is not implemented.") from e

if __name__ == "__main__":
    # Ensure the data directory exists
    if not os.path.exists(args.data_dir):
        raise FileNotFoundError(f"Data directory {args.data_dir} does not exist.")
    
    main()

