<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\Rules;
use Inertia\Inertia;
use Inertia\Response;
use Illuminate\Http\JsonResponse;

class StockController extends Controller
{
    public function create(Request $request): JsonResponse
    {
        $data = $request->all();

        // Zapis do pliku JSON
        $filename = 'requests/' . date('Y-m-d_H-i-s') . '_request.json';
        Storage::disk('local')->put($filename, json_encode($data, JSON_PRETTY_PRINT));

        return response()->json([
            'message' => 'Stock creation endpoint',
            'data' => $data
        ]);
    }
}
