# python version 1.0						DO NOT EDIT
#
# Generated by smidump version 0.4.8:
#
#   smidump -f python OLD-CISCO-CPU-MIB

FILENAME = "OLD-CISCO-CPU-MIB.my"

MIB = {
    "moduleName" : "OLD-CISCO-CPU-MIB",

    "OLD-CISCO-CPU-MIB" : {
        "nodetype" : "module",
        "language" : "SMIv1",
    },

    "imports" : (
        {"module" : "", "name" : "OBJECT-TYPE"},
        {"module" : "CISCO-SMI", "name" : "local"},
    ),

    "nodes" : {
        "lcpu" : {
            "nodetype" : "node",
            "moduleName" : "OLD-CISCO-CPU-MIB",
            "oid" : "1.3.6.1.4.1.9.2.1",
        }, # node
        "busyPer" : {
            "nodetype" : "scalar",
            "moduleName" : "OLD-CISCO-CPU-MIB",
            "oid" : "1.3.6.1.4.1.9.2.1.56",
            "status" : "current",
            "syntax" : {
                "type" : { "module" :"", "name" : "Integer32"},
            },
            "access" : "readonly",
            "description" :
                """CPU busy percentage in the last 5 second
period. Not the last 5 realtime seconds but
the last 5 second period in the scheduler.""",
        }, # scalar
        "avgBusy1" : {
            "nodetype" : "scalar",
            "moduleName" : "OLD-CISCO-CPU-MIB",
            "oid" : "1.3.6.1.4.1.9.2.1.57",
            "status" : "current",
            "syntax" : {
                "type" : { "module" :"", "name" : "Integer32"},
            },
            "access" : "readonly",
            "description" :
                """1 minute exponentially-decayed moving
average of the CPU busy percentage.""",
        }, # scalar
        "avgBusy5" : {
            "nodetype" : "scalar",
            "moduleName" : "OLD-CISCO-CPU-MIB",
            "oid" : "1.3.6.1.4.1.9.2.1.58",
            "status" : "current",
            "syntax" : {
                "type" : { "module" :"", "name" : "Integer32"},
            },
            "access" : "readonly",
            "description" :
                """5 minute exponentially-decayed moving
average of the CPU busy percentage.""",
        }, # scalar
        "idleCount" : {
            "nodetype" : "scalar",
            "moduleName" : "OLD-CISCO-CPU-MIB",
            "oid" : "1.3.6.1.4.1.9.2.1.59",
            "status" : "current",
            "syntax" : {
                "type" : { "module" :"", "name" : "Integer32"},
            },
            "access" : "readwrite",
            "description" :
                """cisco internal variable. not to be used""",
        }, # scalar
        "idleWired" : {
            "nodetype" : "scalar",
            "moduleName" : "OLD-CISCO-CPU-MIB",
            "oid" : "1.3.6.1.4.1.9.2.1.60",
            "status" : "current",
            "syntax" : {
                "type" : { "module" :"", "name" : "Integer32"},
            },
            "access" : "readwrite",
            "description" :
                """cisco internal variable. not to be used""",
        }, # scalar
    }, # nodes

}
