# FR-USR-01: Directory Layout and User Cards

The User Directory screen lists all active users of the QPilot admin portal as a
grid of cards.

- Each card shows the user's name, email, role badge, and status (Active/Inactive).
- The grid loads 20 cards per page with pagination controls at the bottom.
- A search box above the grid filters cards by name or email as the admin types
  (client-side, no page reload).
- Clicking a card opens the user's detail panel in a slide-over on the right.
- If no users match the search, the grid shows an empty state with the text
  "No users found" and a "Clear search" link.
- Inactive users are shown with a greyed-out card and an "Inactive" badge; admins
  cannot open the detail panel for inactive users from the card (a lock icon is
  shown instead).
