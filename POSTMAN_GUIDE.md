# Postman Testing Guide

I have generated a Postman Collection to make testing your new API easy.

## 1. Import instructions
1. Open **Postman**.
2. Click the **Import** button (top left).
3. Drag and drop the `turf_management_postman.json` file from the project root.

## 2. Environment Setup
The collection has a variable `baseUrl` set to `http://127.0.0.1:8000` by default.

## 3. Authentication Flow
1. Run the **Login (Owner)** or **Login (Customer)** request.
2. Copy the `access` token from the response.
3. In Postman, go to the **Collection** settings (Turf Management SaaS API) -> **Variables** tab.
4. Paste the token into the `access_token` variable's "Current Value".
5. All other requests will now be automatically authenticated.

## 4. Key Endpoints to Test
- **Create Booking (Nested)**: Uses the new `/api/tenants/1/bookings/` path.
- **Dashboard**: Test `today-revenue` or `today-bookings`.
- **Double Booking**: Try running the `Create Booking` request twice for the same date/slot to see the `400 Bad Request` validation.

## 5. Mock Data JSON (Reference)
If you want to manually create requests, here is the structure:

### Create Booking
```json
{
    "court": 1,
    "slot": 1,
    "date": "2024-12-05"
}
```

### Create Slot
```json
{
    "court": 1,
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "price": "1500.00",
    "is_active": true
}
```
