import cairosvg
import os
# Define the input SVG file and output PDF file paths

input_svg = "C:/Users/Butch/Desktop/OneDrive - Stony Brook University/TON/paper_fig/comprehensive_comparison/QFT_5_limitQPU_comparison.svg"
output_pdf ="C:/Users/Butch/Desktop/OneDrive - Stony Brook University/TON/paper_pdf/comprehensive_comparison/QFT_5_limitQPU_comparison.pdf"
os.makedirs(output_pdf, exist_ok=True)
cairosvg.svg2pdf(url=input_svg, write_to=output_pdf)