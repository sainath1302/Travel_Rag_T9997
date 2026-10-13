import json
from pathlib import Path


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DOCUMENT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "rag_documents.json"
)


# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_documents():

    if not DOCUMENT_FILE.exists():

        raise FileNotFoundError(
            f"File not found: {DOCUMENT_FILE}"
        )

    with open(
        DOCUMENT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# VALIDATE DOCUMENTS
# ============================================================

def validate_documents(documents):

    print("=" * 60)
    print("TRAVEL RAG - DOCUMENT VALIDATION")
    print("=" * 60)

    print(
        f"\nTotal documents: {len(documents)}"
    )

    required_fields = [
        "id",
        "destination_id",
        "destination_name",
        "state",
        "region",
        "text",
        "metadata"
    ]

    errors = []

    empty_documents = []

    duplicate_ids = []

    ids = []

    # --------------------------------------------------------
    # CHECK EACH DOCUMENT
    # --------------------------------------------------------

    for index, document in enumerate(documents):

        # Check required fields
        for field in required_fields:

            if field not in document:

                errors.append(
                    f"Document {index}: "
                    f"missing '{field}'"
                )

        # Check text
        text = document.get("text", "")

        if not isinstance(text, str):

            errors.append(
                f"Document {index}: text is not a string"
            )

        elif len(text.strip()) == 0:

            empty_documents.append(index)

        # Check ID
        document_id = document.get("id")

        if document_id in ids:

            duplicate_ids.append(document_id)

        ids.append(document_id)

    # --------------------------------------------------------
    # PRINT RESULTS
    # --------------------------------------------------------

    print("\nRequired field check:")

    if errors:

        print(f"FAILED — {len(errors)} problems found.")

        for error in errors[:20]:

            print(f"  - {error}")

    else:

        print("PASSED")

    print("\nEmpty document check:")

    if empty_documents:

        print(
            f"FAILED — {len(empty_documents)} empty documents."
        )

    else:

        print("PASSED")

    print("\nDuplicate ID check:")

    if duplicate_ids:

        print(
            f"FAILED — {len(duplicate_ids)} duplicate IDs."
        )

        print(
            duplicate_ids[:20]
        )

    else:

        print("PASSED")

    # --------------------------------------------------------
    # TEXT STATISTICS
    # --------------------------------------------------------

    lengths = [
        len(
            document.get("text", "")
        )
        for document in documents
    ]

    if lengths:

        print("\nDocument size statistics:")

        print(
            f"Minimum characters: {min(lengths)}"
        )

        print(
            f"Maximum characters: {max(lengths)}"
        )

        print(
            f"Average characters: "
            f"{sum(lengths) / len(lengths):.2f}"
        )

    # --------------------------------------------------------
    # SHOW SAMPLE DOCUMENT
    # --------------------------------------------------------

    if documents:

        sample = documents[0]

        print("\n" + "=" * 60)
        print("SAMPLE DOCUMENT")
        print("=" * 60)

        print(
            f"\nID: {sample.get('id')}"
        )

        print(
            f"Destination: "
            f"{sample.get('destination_name')}"
        )

        print(
            f"State: "
            f"{sample.get('state')}"
        )

        print(
            f"Region: "
            f"{sample.get('region')}"
        )

        print("\nText:")
        print("-" * 60)

        print(
            sample.get("text", "")
        )

        print("-" * 60)

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    if (
        not errors
        and not empty_documents
        and not duplicate_ids
    ):

        print("\n" + "=" * 60)
        print("DOCUMENT VALIDATION SUCCESSFUL")
        print("=" * 60)

    else:

        print("\n" + "=" * 60)
        print("DOCUMENT VALIDATION FOUND PROBLEMS")
        print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    documents = load_documents()

    validate_documents(
        documents
    )