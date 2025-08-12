             PGM        PARM(&LIB &IFSDIR &OUTQ)
             DCL        VAR(&LIB) TYPE(*CHAR) LEN(10)
             DCL        VAR(&IFSDIR) TYPE(*CHAR) LEN(256)
             DCL        VAR(&OUTQ) TYPE(*CHAR) LEN(10)
             DCL        VAR(&STATUS) TYPE(*CHAR) LEN(7) VALUE('FAILED')
             DCL        VAR(&MARKER) TYPE(*CHAR) LEN(300)

             CHGVAR     VAR(&MARKER) VALUE(&IFSDIR *TCAT '/run/RUN' *TCAT %SST(%TIMESTAMP():1:14) *TCAT '.status')

             /* Import CSV into staging */
             CPYFRMIMPF FROMSTMF(&IFSDIR *TCAT '/in/' *TCAT 'data.csv') +
                          TOFILE(&LIB/STG_IN) MBROPT(*REPLACE) RCDDLM(*LF) +
                          STRDLM(*NONE) RPLNULLVAL(*FLDDFT)
             MONMSG     MSGID(CPF0000) EXEC(GOTO CMDLBL(WRITE))

             /* Apply SQL logic */
             RUNSQLSTM  SRCSTMF(&IFSDIR *TCAT '/scripts/apply.sql') +
                          SETVAR((LIB_STG &LIB))
             MONMSG     MSGID(CPF0000) EXEC(GOTO CMDLBL(WRITE))

             /* Export results */
             CPYTOIMPF FROMFILE(&LIB/SHADOW_PAYROLL) +
                          TOSTMF(&IFSDIR *TCAT '/out/data_result.csv') +
                          MBROPT(*REPLACE) STMFCCSID(1208)
             MONMSG     MSGID(CPF0000)

             CHGVAR     VAR(&STATUS) VALUE('SUCCESS')

WRITE:       QSH        CMD('echo ' *CAT &STATUS *TCAT ' > ' *CAT &MARKER)
             ENDPGM
