TEXDIR  := paper
BUILD   := build
BASE    := paper
SRC     := $(TEXDIR)/$(BASE).tex
OUT     := $(BASE).pdf

# Export TEXINPUTS so all sub-processes (pdflatex, bibtex) see it
export TEXINPUTS := .:./$(TEXDIR):

all: $(OUT)

$(OUT): $(SRC) $(TEXDIR)/*.tex
	@mkdir -p $(BUILD)
	# Run LaTeX once to generate the .aux
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=$(BUILD) $(SRC)
	# Run BibTeX - ignore error with '-' if no citations exist yet
	-bibtex $(BUILD)/$(BASE)
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=$(BUILD) $(SRC)
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=$(BUILD) $(SRC)
	@if [ -f $(BUILD)/$(BASE).pdf ]; then \
		cp $(BUILD)/$(BASE).pdf ./$(OUT); \
	else \
		echo "PDF not found in $(BUILD)/"; exit 1; \
	fi

clean:
	rm -rf $(BUILD)
	rm -f $(OUT)

.PHONY: all clean
