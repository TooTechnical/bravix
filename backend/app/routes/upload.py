from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.parsers import parse_file

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handles file uploads for the Bravix AI Financial Analyzer.
    Receives a PDF, CSV, Excel, or Word file and passes it to the parser.
    """
    try:
        # The parse_file function handles file reading and content extraction
        parsed_data = parse_file(file)

        # Return parsed financial data to the frontend
        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": parsed_data
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or unsupported file format: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File parsing failed: {str(e)}"
        )
