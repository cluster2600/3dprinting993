.PHONY: check validate test twin twin-validate container-recon container-cadsim container-smoke container-push

REGISTRY ?= ghcr.io/cluster2600
IMAGE_TAG ?= dev

check: validate test

validate:
	python3 scripts/validate_catalog.py
	python3 scripts/validate_sources.py
	python3 scripts/validate_measurements.py
	python3 scripts/validate_reference.py
	python3 scripts/validate_manual_measurements.py
	python3 scripts/validate_twin.py

test:
	python3 -m unittest discover -s tests -v

twin:
	python3 scripts/twin_coverage.py

twin-validate:
	python3 scripts/validate_twin.py

container-recon:
	docker build -f containers/recon.Dockerfile -t 3dprinting993-recon:$(IMAGE_TAG) .

container-cadsim:
	docker build -f containers/cadsim.Dockerfile -t 3dprinting993-cadsim:$(IMAGE_TAG) .

container-smoke:
	docker run --rm 3dprinting993-recon:$(IMAGE_TAG) smoke-test.sh recon
	docker run --rm 3dprinting993-cadsim:$(IMAGE_TAG) smoke-test.sh cadsim

container-push:
	docker tag 3dprinting993-recon:$(IMAGE_TAG) $(REGISTRY)/3dprinting993-recon:$(IMAGE_TAG)
	docker tag 3dprinting993-cadsim:$(IMAGE_TAG) $(REGISTRY)/3dprinting993-cadsim:$(IMAGE_TAG)
	docker push $(REGISTRY)/3dprinting993-recon:$(IMAGE_TAG)
	docker push $(REGISTRY)/3dprinting993-cadsim:$(IMAGE_TAG)
