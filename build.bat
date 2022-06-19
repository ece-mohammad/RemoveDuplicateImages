@ECHO off
CALL venv\Scripts\activate

IF "%1%" == "dev" ( GOTO BUILD_DEV ) ELSE ( GOTO BUILD_DIST )

:BUILD_DIST

ECHO ---------------------------------------------------------------------------
ECHO Building executable for distribution...
ECHO ---------------------------------------------------------------------------

pyinstaller --clean --noconfirm specs\remove_duplicate_images.spec

GOTO ZIP_EXECUTABLE

@REM ---------------------------------------------------------------------------

:BUILD_DEV

ECHO ---------------------------------------------------------------------------
ECHO Building executable for development...
ECHO ---------------------------------------------------------------------------

pyinstaller --clean --noconfirm specs\remove_duplicate_images.spec

GOTO ZIP_EXECUTABLE

@REM ---------------------------------------------------------------------------

:ZIP_EXECUTABLE

ECHO ---------------------------------------------------------------------------
ECHO Executable build finished...
ECHO ---------------------------------------------------------------------------

pushd dist

ECHO ---------------------------------------------------------------------------
ECHO Archiving the executable...
ECHO ---------------------------------------------------------------------------

DEL MindustryLogicEditor_Winx64.zip
CALL zip -u -r -1 remove_duplicate_images.zip remove_duplicate_images.exe
popd

ECHO ---------------------------------------------------------------------------
ECHO Done...
ECHO ---------------------------------------------------------------------------
