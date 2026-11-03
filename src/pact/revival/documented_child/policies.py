"""CPU policy/analysis binding; evaluation payloads never enter allocations."""
from ...util import digest
from ..allocation_v3 import design
from ..gpqa_source import contracts, results, sources


def freeze(training, scores, accepted, method_digest):
    contract=contracts.allocation_inputs(training)
    probes={f:[r['task']['task_id'] for r in contract['records']
               if r['split']=='allocation_probe' and r['family']==f] for f in design.SOURCES}
    # Credit computation enforces instruments and missingness with the original
    # scorer contract. No outcome filtering or evaluation-based policy choice.
    values=design.credits(scores,contract['blocks'],probes,accepted)
    policies=design.compile_policies(contract['blocks'],values['terminal'],values['private_bank'],
        contract['shuffle'],contract['s0'],{'child_method_digest':method_digest,
                                         'training_dependency_hash':digest(contract)})
    return {'policies':policies,'credits':values,'training_dependency_hash':digest(contract),
            'method_digest':method_digest,'allocation_source_weights':design.SOURCE_WEIGHTS,
            'evaluation_source_weights':dict.fromkeys(sources.SOURCES_EVAL,.5),
            'analysis_digest':digest(design.ANALYSIS),'execution_authorized':False}


def report(candidate, outcomes):
    """Existing source-stratified missingness and paired analysis; no pooling calls."""
    return results.report(candidate,outcomes)
