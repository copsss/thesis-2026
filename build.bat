@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   南开大学论文编译脚本
echo ========================================
echo.

:: 设置文件名
set MAIN=main

:: 清理旧文件
echo [1/5] 清理辅助文件...
del /q *.aux *.out *.blg *.toc *.bbl *.bcf *.log *.fls *.fdb_latexmk *.synctex.gz *.run.xml 2>nul
del /q abstract.aux chapter1.aux chapter2.aux chapter3.aux chapter4.aux chapter5.aux 2>nul
del /q references.aux acknowledgements.aux resume.aux 2>nul
echo      完成！

:: 第一次编译
echo.
echo [2/5] 第一次 XeLaTeX 编译...
xelatex -synctex=1 -interaction=nonstopmode -file-line-error %MAIN%.tex
if errorlevel 1 (
    echo      编译失败！请检查错误信息。
    pause
    exit /b 1
)
echo      完成！

:: Biber 处理参考文献
echo.
echo [3/5] Biber 处理参考文献...
biber %MAIN%
if errorlevel 1 (
    echo      Biber 处理失败！
    pause
    exit /b 1
)
echo      完成！

:: 第二次编译
echo.
echo [4/5] 第二次 XeLaTeX 编译...
xelatex -synctex=1 -interaction=nonstopmode -file-line-error %MAIN%.tex
if errorlevel 1 (
    echo      编译失败！
    pause
    exit /b 1
)
echo      完成！

:: 第三次编译
echo.
echo [5/5] 第三次 XeLaTeX 编译（交叉引用）...
xelatex -synctex=1 -interaction=nonstopmode -file-line-error %MAIN%.tex
if errorlevel 1 (
    echo      编译失败！
    pause
    exit /b 1
)
echo      完成！

:: 最终清理
echo.
echo ========================================
echo   编译成功！生成 %MAIN%.pdf
echo ========================================
echo.
echo 正在清理辅助文件...
del /q *.aux *.out *.blg *.toc *.bbl *.bcf *.log *.fls *.fdb_latexmk *.synctex.gz *.run.xml 2>nul
del /q abstract.aux chapter1.aux chapter2.aux chapter3.aux chapter4.aux chapter5.aux 2>nul
del /q references.aux acknowledgements.aux resume.aux 2>nul

echo 清理完成！
echo.
pause
