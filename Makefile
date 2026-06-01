PROTO_PATH = ../../../../protos/source
PYTHON_OUT = burger/infrastructure/kds

install:
	pip3 install -r requirements.txt
	apt-get install libzbar-dev

grpcgen:
	python3 -m grpc_tools.protoc --proto_path=$(PROTO_PATH) --python_out=$(PYTHON_OUT) --grpc_python_out=$(PYTHON_OUT) --pyi_out=$(PYTHON_OUT) $(PROTO_PATH)/validate/validate.proto
	python3 -m grpc_tools.protoc --proto_path=$(PROTO_PATH) --python_out=$(PYTHON_OUT) --grpc_python_out=$(PYTHON_OUT) --pyi_out=$(PYTHON_OUT) $(PROTO_PATH)/includes/burgerbot_common.proto
	python3 -m grpc_tools.protoc --proto_path=$(PROTO_PATH) --python_out=$(PYTHON_OUT) --grpc_python_out=$(PYTHON_OUT) --pyi_out=$(PYTHON_OUT) $(PROTO_PATH)/services/burgerbot/connector.proto

dbgen:
	mkdir -p db
	rm -f db/burger.db
	sqlite3 db/burger.db < ../sql/burger_table.sql
	sqlite3 db/burger.db < ../sql/burger_data.sql

run:
	python3 main.py