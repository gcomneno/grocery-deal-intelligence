# Unsupported-claim minimization decision gate

The fixed-corpus baseline after deterministic grounding is 0 contradicted, 42 supported, and 29 unverifiable claims, with all 20 critical claims supported and 4/4 records admitted.

Before prompt or runtime changes, the current canonical schema imposes a hard constraint: several structures are required, and required provenance fields have no null/unknown representation. Therefore "omit every unsupported claim" is not expressible while still producing a schema-valid Grocery Offer v0.1 object in all cases.

The next implementation step must first classify the 29 unverifiable claims by whether the schema permits omission or conservative uncertainty. Prompt minimization is allowed only for claims whose omission/uncertainty remains schema-valid. Claims forced by the schema without an uncertainty representation must remain visible as a contract tension rather than being fabricated or hidden.
