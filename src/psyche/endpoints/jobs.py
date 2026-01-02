from enum import Enum
from fastapi import APIRouter, HTTPException
from psyche.fastapi_deps import JobManagerDep
from psyche.schemas.job_schemas import JobRead, JobBatchRequest

router = APIRouter(prefix="/jobs")

jobs_tags: list[str | Enum] = ["Jobs"]

@router.get("", response_model=list[JobRead], tags=jobs_tags)
async def get_jobs(job_manager: JobManagerDep):
  return job_manager.get_jobs()

@router.post("/batch", response_model=list[JobRead], tags=jobs_tags)
async def get_job_batch(payload: JobBatchRequest, job_manager: JobManagerDep):
  return job_manager.get_jobs_by_ids(payload.job_ids)

@router.get("/{job_id}", response_model=JobRead, tags=jobs_tags)
async def get_job(job_id: int, job_manager: JobManagerDep):
  job = job_manager.get_job(job_id)
  if job is None:
    raise HTTPException(status_code=404, detail="Job not found")
  return job
