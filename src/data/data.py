from re import U
import pandas as pd
import datasets
from sklearn.model_selection import train_test_split
from src.utils.ErrorHandler import ErrorHandler

# -- internal
from src.utils.FileManager import FileManager


# ===============================================================================================
# LOADING
def load_imdb(train_size=1.0, seed=None):
    """
    Load the dataset "IMDB" as train and test DataFrames.
    
    Parameters:
        train_size : (float)
            Percentage of the dataset that will be used as "train" data. 
        
        seed : (int, optional)
            Seed determinist of the "random" split. If "None", use cfg seed
        
    Returns:
        pd.DataFrame : training set
        pd.DataFrame : testing set
    """
    
    # load dataset and return Train/Test as DataFrames
    ds      = datasets.load_dataset("imdb")
    train   = ds["train"].to_pandas()
    test    = ds["test"].to_pandas()
    
    # clean dataset before returning
    for df in (train, test):
        df["text"] = (df["text"].str.replace("<br />", " ", regex=False)
                                .str.replace("\n", " ", regex=False)
                                .str.strip())
    
    # reduce training set size if requested
    if train_size < 1.0:
        if seed == None:
            seed = FileManager.load_config()["seed"]
        train, _ = train_test_split(train, train_size=train_size, random_state=seed, stratify=train["label"]) 

    return train, test


# ===============================================================================================
# PREPARING
def prepare_dataset(dataset_name: str, tokenizer, max_length: int):    
    # load train / test dataframes
    if dataset_name == "imdb":
        train_df, test_df = load_imdb()
        return tokenize_data(train_df, tokenizer, max_length), tokenize_data(train_df, tokenizer, max_length)
    
    ErrorHandler.fatal("Unhandled dataset : " + dataset_name);
    

def tokenize_data(df: pd.DataFrame, tokenizer, max_length: int):
    """
    Use the model's Tokenize to convert DataFrame into a tokenized dataset ready for training
    
    Args:
        df (DataFrame) : original data frame containing raw data
    """
    
    # CHECK : expected columns
    if "text" not in df.columns:
        ErrorHandler.fatal("unable to find the column 'text' in the provided dataframe")
    if "label" not in df.columns:
        ErrorHandler.fatal("unable to find the column 'label' in the provided dataframe")

    # method that tokenize texts in the dataframe by batch
    def tok(batch):
        return tokenizer(batch["text"], truncation=True, padding=True, max_length=max_length)
    
    # convert Dataframe into Dataset
    tokenized_ds = datasets.Dataset.from_pandas(df)
    # convert text into tokens
    tokenized_ds = tokenized_ds.map(tok, batched=True)
    # rename label columns
    tokenized_ds = tokenized_ds.rename_column("label", "labels").with_format("torch")
    
    # return dataset ready for training
    return tokenized_ds


# ===============================================================================================
# TESTING & EVALUATING data
def describe_dataset(df: pd.DataFrame):
    """
    Extract most important information of the dataset (as DataFrame) to have a quick overview.
    
    Args:
        df : (pd.DataFrame)
            DataFrame to Analyse

    Returns:
        dict : dictionnary containing the following information
            - n_samples (int): Total number of samples in the dataframe.
            - class_balance (dict): Relative frequency of each class 
              (keys = class labels, values = proportions in [0, 1]).
            - n_tokens_mean (float): Mean number of tokens per text 
              (whitespace split).
            - n_tokens_std (float): Standard deviation of token counts.
            - n_tokens_p95 (float): 95th percentile of token counts 
              (useful for max sequence length).
    """
    lengths = df["text"].str.split().apply(len)
    return {
        "n_samples":        len(df),
        "class_balance":    df["label"].value_counts(normalize=True).to_dict(),
        "n_tokens_mean":    float(lengths.mean()),
        "n_tokens_std":     float(lengths.std()),
        "n_tokens_p95":     float(lengths.quantile(0.95)),
    }