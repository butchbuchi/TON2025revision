@REM @echo off

@REM @REM echo Running Rd FT extra=1 > FT_parallel_running/run2_Rd_ft_extra1.log
@REM @REM python "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --FT_mode --extra_space 1 >> FT_parallel_running/run2_Rd_ft_extra1.log 2>&1


@REM echo Running Rd FT TRANS extra=1 > FT_parallel_running/run4_Rd_ft_trans_extra1.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --FT_mode --trans --extra_space 1 >> FT_parallel_running/run4_Rd_ft_trans_extra1.log 2>&1


@REM echo Running Rd FT extra=0 > FT_parallel_running/run6_Rd_ft_extra0.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --FT_mode --extra_space 0 >> FT_parallel_running/run6_Rd_ft_extra0.log 2>&1


@REM echo Running Rd FT TRANS extra=0 > FT_parallel_running/run8_Rd_ft_trans_extra0.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --FT_mode --trans --extra_space 0 >> FT_parallel_running/run8_Rd_ft_trans_extra0.log 2>&1

@REM echo All experiments completed!
@REM pause


@echo off
setlocal enabledelayedexpansion

set logdir=FT_parallel_running

:: Run 1

echo Running Rd FT TRANS extra=1 > %logdir%/run4_Rd_ft_trans_extra1.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
  --circuit_type "Rd" --FT_mode --trans --extra_space 1 ^
  >> %logdir%/run4_Rd_ft_trans_extra1.log 2>&1
if errorlevel 1 echo [Error] run4 failed. & pause & exit /b

:: Run 2

echo Running Rd FT extra=0 > %logdir%/run6_Rd_ft_extra0.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
  --circuit_type "Rd" --FT_mode --extra_space 0 ^
  >> %logdir%/run6_Rd_ft_extra0.log 2>&1
if errorlevel 1 echo [Error] run6 failed. & pause & exit /b

:: Run 3

echo Running Rd FT TRANS extra=0 > %logdir%/run8_Rd_ft_trans_extra0.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
  --circuit_type "Rd" --FT_mode --trans --extra_space 0 ^
  >> %logdir%/run8_Rd_ft_trans_extra0.log 2>&1
if errorlevel 1 echo [Error] run8 failed. & pause & exit /b

:: Final message

echo All experiments completed!
pause
