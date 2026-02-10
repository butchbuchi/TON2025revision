@REM @echo off

@REM echo Running Rd FT extra=1 > FT_parallel_running_PGmode/run2_Rd_ft_extra1.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --PG_mode --FT_mode --extra_space 1 >> FT_parallel_running_PGmode/run2_Rd_ft_extra1.log 2>&1


@REM echo Running Rd FT TRANS extra=1 > FT_parallel_running_PGmode/run4_Rd_ft_trans_extra1.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --PG_mode --FT_mode --trans --extra_space 1 >> FT_parallel_running_PGmode/run4_Rd_ft_trans_extra1.log 2>&1


@REM echo Running Rd FT extra=0 > FT_parallel_running_PGmode/run6_Rd_ft_extra0.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --PG_mode --FT_mode --extra_space 0 >> FT_parallel_running_PGmode/run6_Rd_ft_extra0.log 2>&1


@REM echo Running Rd FT TRANS extra=0 > FT_parallel_running_PGmode/run8_Rd_ft_trans_extra0.log
@REM python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" --circuit_type "Rd" --PG_mode --FT_mode --trans --extra_space 0 >> FT_parallel_running_PGmode/run8_Rd_ft_trans_extra0.log 2>&1

@REM echo All experiments completed!
@REM pause

@echo off
setlocal enabledelayedexpansion



:: 设置日志文件夹变量
set logdir=FT_parallel_running_PGmode


echo Running Rd FT extra=1 > %logdir%/run2_Rd_ft_extra1.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
    --circuit_type "Rd" --PG_mode --FT_mode --extra_space 1 ^
    >> %logdir%/run2_Rd_ft_extra1.log 2>&1
if errorlevel 1 echo [Error] run2 failed. & pause & exit /b


echo Running Rd FT TRANS extra=1 > %logdir%/run4_Rd_ft_trans_extra1.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
    --circuit_type "Rd" --PG_mode --FT_mode --trans --extra_space 1 ^
    >> %logdir%/run4_Rd_ft_trans_extra1.log 2>&1
if errorlevel 1 echo [Error] run4 failed. & pause & exit /b


echo Running Rd FT extra=0 > %logdir%/run6_Rd_ft_extra0.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
    --circuit_type "Rd" --PG_mode --FT_mode --extra_space 0 ^
    >> %logdir%/run6_Rd_ft_extra0.log 2>&1
if errorlevel 1 echo [Error] run6 failed. & pause & exit /b


echo Running Rd FT TRANS extra=0 > %logdir%/run8_Rd_ft_trans_extra0.log
python -u "C:\Users\Butch\Desktop\OneDrive - Stony Brook University\TON\multi_processing.py" ^
    --circuit_type "Rd" --PG_mode --FT_mode --trans --extra_space 0 ^
    >> %logdir%/run8_Rd_ft_trans_extra0.log 2>&1
if errorlevel 1 echo [Error] run8 failed. & pause & exit /b

echo All experiments completed!
pause
