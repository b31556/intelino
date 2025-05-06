import requests

def route_trains(train_id, destination):
    """
    Route the train to the destination.
    :param train_id: The ID of the train to route. ids start from 0.
    :param destination: The destination for the train. This should be a string. Looks like a station name.
    :return: The response from the server.
            """
    # Send the data to the server
    response = requests.post(f'http://localhost:5080/set_plan/{train_id}', data=destination)
    return response.text




while True:

    input_data = input("Chose train id (or 'exit' to quit): ")
    if input_data.lower() == 'exit':
        break
    input_destination = input("Chose destination: ")
    if input_destination.lower() == 'exit':
        break

    # Send the data to the server
    response = requests.post(f'http://localhost:5080/set_plan/{input_data}', data=input_destination)
    print(response.text)
    # Print the server's response