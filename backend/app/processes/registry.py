"""Every business process the system knows. Adding one means adding it to this tuple."""

from backend.app.processes import askoe, commerce, ip, nonstandard, ses, standard
from backend.app.processes.definition import ProcessDefinition

PROCESSES: dict[str, ProcessDefinition] = {
    process.name: process
    for process in (
        ses.PROCESS,
        askoe.PROCESS,
        standard.PROCESS,
        nonstandard.PROCESS,
        ip.PROCESS,
        commerce.PROCESS,
    )
}
