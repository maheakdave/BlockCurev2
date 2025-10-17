import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers.pipelines.token_classification import TokenClassificationPipeline
import spacy
from spacy.matcher import Matcher
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import tensorflow as tf

model_checkpoint = "Davlan/bert-base-multilingual-cased-ner-hrl"
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
model = AutoModelForTokenClassification.from_pretrained(model_checkpoint)
class TokenClassificationChunkPipeline(TokenClassificationPipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def preprocess(self, sentence, offset_mapping=None, **preprocess_params):
        tokenizer_params = preprocess_params.pop("tokenizer_params", {})
        truncation = True if self.tokenizer.model_max_length and self.tokenizer.model_max_length > 0 else False
        inputs = self.tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            return_special_tokens_mask=True,
            return_offsets_mapping=True,
            return_overflowing_tokens=True,  # Return multiple chunks
            max_length=self.tokenizer.model_max_length,
            padding=True
        )
        #inputs.pop("overflow_to_sample_mapping", None)
        num_chunks = len(inputs["input_ids"])

        for i in range(num_chunks):
            if self.framework == "tf":
                model_inputs = {k: tf.expand_dims(v[i], 0) for k, v in inputs.items()}
            else:
                model_inputs = {k: v[i].unsqueeze(0) for k, v in inputs.items()}
            if offset_mapping is not None:
                model_inputs["offset_mapping"] = offset_mapping
            model_inputs["sentence"] = sentence if i == 0 else None
            model_inputs["is_last"] = i == num_chunks - 1
            yield model_inputs

    def _forward(self, model_inputs):
        # Forward
        special_tokens_mask = model_inputs.pop("special_tokens_mask")
        offset_mapping = model_inputs.pop("offset_mapping", None)
        sentence = model_inputs.pop("sentence")
        is_last = model_inputs.pop("is_last")

        overflow_to_sample_mapping = model_inputs.pop("overflow_to_sample_mapping")

        output = self.model(**model_inputs)
        logits = output["logits"] if isinstance(output, dict) else output[0]


        model_outputs = {
            "logits": logits,
            "special_tokens_mask": special_tokens_mask,
            "offset_mapping": offset_mapping,
            "sentence": sentence,
            "overflow_to_sample_mapping": overflow_to_sample_mapping,
            "is_last": is_last,
            **model_inputs,
        }

        # We reshape outputs to fit with the postprocess inputs
        model_outputs["input_ids"] = torch.reshape(model_outputs["input_ids"], (1, -1))
        model_outputs["token_type_ids"] = torch.reshape(model_outputs["token_type_ids"], (1, -1))
        model_outputs["attention_mask"] = torch.reshape(model_outputs["attention_mask"], (1, -1))
        model_outputs["special_tokens_mask"] = torch.reshape(model_outputs["special_tokens_mask"], (1, -1))
        model_outputs["offset_mapping"] = torch.reshape(model_outputs["offset_mapping"], (1, -1, 2))

        return model_outputs



pipe = TokenClassificationChunkPipeline(model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Replace entities
def anonymize(text):
    ents = pipe(text)
    split_text = list(text)
    for ent in ents:
        #split_text[ent['start']] = f"[{ent['entity_group']}]"
        split_text[ent['start']] = f"*****"
        for i in range(ent['start'] + 1, ent['end']):
            split_text[i] = ""

    return "".join(split_text)

nlp = spacy.load("en_core_web_sm")
def magic(text,nlp = nlp):
    text = anonymize(text)
#nlp = en_core_web_sm.load()
    matcher1 = Matcher(nlp.vocab)
    pattern = [{"TEXT":{"REGEX":"[a-zA-Z0-9_.]+@[a-zA-Z0-9_.]+"}}]
    matcher1.add("EMAIL",[pattern])

    nlp = English()
    matcher = PhraseMatcher(nlp.vocab, attr="SHAPE")
    matcher.add("ADMISSION_NUMBER", [nlp("ISP-0000-0000000000")])

    matcher.add("DATE", [nlp("00-00-0000"),nlp("0-00-0000"),nlp("00-0-0000"),nlp("0-0-0000"),nlp("00-00-00"),nlp("0-00-00"),nlp("00-0-00"),nlp("0-0-00"),nlp("0000-00-00")])

    matcher.add("PHONE_NUMBER", [nlp("(+91) 0000-000000"),nlp("(91) 0000-000000"),nlp("0000-000000")])

    doc= nlp(text)
    matches= matcher(doc)
    anonymized=""

    lst =[t.text for t in doc]
    for i in range(len(matches)):
        for j in range(matches[i][1],matches[i][2]):
            lst[j]="**"
    matches= matcher1(doc)
    for i in range(len(matches)):
        for j in range(matches[i][1],matches[i][2]):
            lst[j]="**"
    for ele in lst:
        anonymized+=ele+" "
    return anonymized


class patient(BaseModel):
    id:str
    diagnosis:str
    treatment: str

app = FastAPI()


@app.post("/api")
async def root(record:patient):
    record.treatment = magic(record.treatment)
    jr_d = jsonable_encoder(record)
    return JSONResponse(content=jr_d,status_code=200,media_type="application/json")
