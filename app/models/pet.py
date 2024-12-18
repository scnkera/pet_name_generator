from flask import Blueprint, request, abort, make_response
from ..db import db
from ..models.pet import Pet

import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

bp = Blueprint("pets", __name__, url_prefix="/pets")

@bp.post("")
def create_pet():
    request_body = request.get_json()
    generated_pet_name = generate_pet_name(request_body)
    request_body["name"] = generated_pet_name

    try: 
        new_pet = Pet.from_dict(request_body)
        db.session.add(new_pet)
        db.session.commit()
        return new_pet.to_dict(), 201
    
    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.get("")
def get_pets():
    pet_query = db.select(Pet)

    pets = db.session.scalars(pet_query)
    response = []

    for pet in pets:
        response.append(pet.to_dict())

    return response

@bp.get("/<pet_id>")
def get_single_pet(pet_id):
    pet = validate_model(Pet,pet_id)
    return pet.to_dict()

def generate_pet_name(pet): 
    model = genai.GenerativeModel("gemini-1.5-flash")
    input_message = f"I am the owner of a pet store. We specialize in creating unique personalized pet names. I have a pet that is a {pet["animal"]} who has a {pet["personality"]} personality, and is the {pet["coloration"]} black. Please return one pet name that embodies all of these characteristics."
    response = model.generate_content(input_message)
    response_strip = response.text.strip("\n")
    return response_strip

def validate_model(cls,id):
    try:
        id = int(id)
    except:
        response =  response = {"message": f"{cls.__name__} {id} invalid"}
        abort(make_response(response , 400))

    query = db.select(cls).where(cls.id == id)
    model = db.session.scalar(query)
    if model:
        return model

    response = {"message": f"{cls.__name__} {id} not found"}
    abort(make_response(response, 404))