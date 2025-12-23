from fastapi import APIRouter, HTTPException
from psyche.fastapi_deps import JobManagerDep
from psyche.schemas.common_schemas import JobRead

router = APIRouter(prefix="/jobs")

@router.get("/{job_id}", response_model=JobRead, tags=["Jobs"])
async def get_job(job_id: int, job_manager: JobManagerDep):
  job = job_manager.get_job(job_id)
  if job is None:
    raise HTTPException(status_code=404, detail="Job not found")
  return job
