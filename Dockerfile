# Replace with an owner-verified immutable Python3.13.14 image digest before build.
# No base is invented; ARG is mandatory. No build/download executed during authoring.
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
WORKDIR /app
COPY requirements-cloud.in /app/requirements-cloud.in
# Only after an approved lock is supplied; this direct-pin image is instructional.
RUN python -m pip install --no-cache-dir -r /app/requirements-cloud.in
COPY azure_course /app/azure_course
CMD ["python", "-m", "azure_course.dapr_worker"]
